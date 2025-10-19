import io
from importlib import import_module
from pathlib import Path
from typing import Any, Tuple

import pytest

from tests.utils import reset_app_modules, ensure_multipart_stub

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover - ambiente sem httpx
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def _prepare_client(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Tuple[TestClient, str, Path, "MusicService", Any]:
    runtime_dir = tmp_path / "runtime"
    storage_dir = tmp_path / "storage"
    runtime_dir.mkdir(parents=True, exist_ok=True)

    db_path = runtime_dir / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MUSIC_STORAGE_DIR", str(storage_dir))
    monkeypatch.setenv("FAKE_REDIS", "1")
    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")

    reset_app_modules()

    settings_module = import_module("app.settings")
    if hasattr(settings_module, "get_database_url"):
        settings_module.get_database_url.cache_clear()
    if hasattr(settings_module, "music_storage_dir"):
        settings_module.music_storage_dir.cache_clear()

    import_module("app.database")

    from app import database
    from app.models import Base, User
    from app.services.music_service import MusicService

    Base.metadata.create_all(database.engine)

    with database.SessionLocal() as session:
        user = User(email="artist@example.com")
        session.add(user)
        session.commit()
        user_id = user.id

    music_service = MusicService(storage_dir=storage_dir)

    ensure_multipart_stub()
    app_module = import_module("api.app")

    client = TestClient(app_module.app)
    return client, user_id, storage_dir, music_service, database


def test_upload_and_fetch_music(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, storage_dir, music_service, database = _prepare_client(tmp_path, monkeypatch)

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

    detail_resp = client.get(f"/music/{music_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["title"] == "Meu Som"
    assert detail["transcription"]["transcript_text"].startswith("Transcrição")
    assert len(detail["beats"]) > 0
    assert (storage_dir).exists()
    assert any(storage_dir.iterdir())
