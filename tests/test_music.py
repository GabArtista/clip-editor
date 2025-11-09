import io
from importlib import import_module
from pathlib import Path
from typing import Any, Tuple
from unittest.mock import MagicMock, patch

import pytest

from tests.utils import reset_app_modules, ensure_multipart_stub, install_ai_stubs

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover - ambiente sem httpx
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def _prepare_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, use_s3_mock: bool = False
) -> Tuple[TestClient, str, Path, "MusicService", Any, dict]:
    runtime_dir = tmp_path / "runtime"
    storage_dir = tmp_path / "storage"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    db_path = runtime_dir / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MUSIC_STORAGE_DIR", str(storage_dir))
    if not use_s3_mock:
        monkeypatch.setenv("MUSIC_STORAGE_DRIVER", "local")
    monkeypatch.setenv("FAKE_REDIS", "1")
    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")

    reset_app_modules()
    install_ai_stubs(monkeypatch)

    settings_module = import_module("app.settings")
    if hasattr(settings_module, "get_database_url"):
        settings_module.get_database_url.cache_clear()
    if hasattr(settings_module, "music_storage_dir"):
        settings_module.music_storage_dir.cache_clear()

    import_module("app.database")

    from app import database
    from app.models import Base
    from app.services.music_service import MusicService

    Base.metadata.create_all(database.engine)

    ensure_multipart_stub()
    app_module = import_module("api.app")

    client = TestClient(app_module.app)

    register_resp = client.post(
        "/auth/register",
        json={"email": "artist@example.com", "password": "secret123"},
    )
    assert register_resp.status_code == 201, register_resp.text
    payload = register_resp.json()
    token = payload["access_token"]
    user_id = payload["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    music_service = MusicService(storage_dir=storage_dir)

    return client, user_id, storage_dir, music_service, database, headers


def test_upload_and_fetch_music(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, storage_dir, music_service, database, headers = _prepare_client(tmp_path, monkeypatch)

    from app.services.music_service import MusicMetadata
    from starlette.datastructures import UploadFile

    upload = UploadFile(
        filename="sample.mp3",
        file=io.BytesIO(b"fake-audio-bytes"),
    )

    with database.SessionLocal() as session:
        asset = music_service.create_music_asset(
            session,
            upload,
            MusicMetadata(
                user_id=user_id,
                title="Meu Som",
                declared_genre="trap",
                description="Demo track",
            ),
        )
        music_id = asset.id

    detail_resp = client.get(f"/music/{music_id}", headers=headers)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["title"] == "Meu Som"
    assert detail["transcription"]["transcript_text"].startswith("Transcrição")
    assert len(detail["beats"]) > 0
    
    # Verifica que o arquivo foi armazenado
    # A estrutura varia dependendo do driver (local vs S3)
    # Para local: storage_dir/media/{user_id}/{music_id}/original.mp3
    # Para S3: URL s3://bucket/media/{user_id}/{music_id}/original.mp3
    media_dir = storage_dir / "media" / user_id
    assert media_dir.exists() or any(storage_dir.iterdir())


def test_list_music_assets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, storage_dir, music_service, database, headers = _prepare_client(tmp_path, monkeypatch)

    from app.services.music_service import MusicMetadata
    from starlette.datastructures import UploadFile

    with database.SessionLocal() as session:
        upload_1 = UploadFile(filename="first.mp3", file=io.BytesIO(b"first-audio"))
        asset_one = music_service.create_music_asset(
            session,
            upload_1,
            MusicMetadata(
                user_id=user_id,
                title="Faixa Um",
                declared_genre="trap",
                description="Primeira faixa",
            ),
        )

        upload_2 = UploadFile(filename="second.mp3", file=io.BytesIO(b"second-audio"))
        asset_two = music_service.create_music_asset(
            session,
            upload_2,
            MusicMetadata(
                user_id=user_id,
                title="Faixa Dois",
                declared_genre="funk",
                description="Segunda faixa",
            ),
        )

    resp = client.get("/music", headers=headers)
    assert resp.status_code == 200
    payload = resp.json()
    assert len(payload) == 2
    ids = [item["id"] for item in payload]
    assert set(ids) == {str(asset_one.id), str(asset_two.id)}
    # Ordenado por uploaded_at desc, logo a segunda criação aparece primeiro.
    assert payload[0]["id"] == asset_two.id
    assert payload[0]["title"] == "Faixa Dois"
    assert payload[0]["status"] == "ready"
    assert payload[0]["genre"] == "funk"
