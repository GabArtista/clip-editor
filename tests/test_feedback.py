import io
from importlib import import_module
from pathlib import Path

import pytest

from tests.utils import reset_app_modules, ensure_multipart_stub

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def _prepare_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    music_store = tmp_path / "music_store"
    videos_dir = tmp_path / "videos"
    processed_dir = tmp_path / "processed"
    videos_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)

    db_path = runtime_dir / "app.db"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("MUSIC_STORAGE_DIR", str(music_store))
    monkeypatch.setenv("VIDEOS_DIR", str(videos_dir))
    monkeypatch.setenv("PROCESSED_DIR", str(processed_dir))
    monkeypatch.setenv("FAKE_REDIS", "1")
    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")

    reset_app_modules()

    settings_module = import_module("app.settings")
    if hasattr(settings_module, "get_database_url"):
        settings_module.get_database_url.cache_clear()
    if hasattr(settings_module, "music_storage_dir"):
        settings_module.music_storage_dir.cache_clear()
    if hasattr(settings_module, "video_storage_dir"):
        settings_module.video_storage_dir.cache_clear()
    if hasattr(settings_module, "processed_storage_dir"):
        settings_module.processed_storage_dir.cache_clear()

    import_module("app.database")

    from app import database
    from app.models import Base
    from app.services.music_service import MusicMetadata, MusicService
    from starlette.datastructures import UploadFile

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

    music_service = MusicService(storage_dir=music_store)
    with database.SessionLocal() as session:
        upload = UploadFile(filename="track.mp3", file=io.BytesIO(b"fake-audio"))
        asset = music_service.create_music_asset(
            session,
            upload,
            MusicMetadata(
                user_id=user_id,
                title="Track",
                declared_genre="trap",
                description="unit-test",
            ),
        )
        music_id = asset.id

    return client, user_id, music_id, database, headers


def test_music_feedback_creates_learning_event(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_id, database, headers = _prepare_environment(tmp_path, monkeypatch)

    response = client.post(
        f"/feedback/music/{music_id}",
        json={
            "message": "Gostei da batida.",
            "mood": "positive",
            "tags": ["batida", "energia"],
            "source": "test",
            "weight": 1.5,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert "id" in payload

    from app.models import MusicFeedback, AILearningEvent, GlobalGenreProfile

    with database.SessionLocal() as session:
        feedback = session.query(MusicFeedback).filter(MusicFeedback.id == payload["id"]).first()
        assert feedback is not None
        event = session.query(AILearningEvent).filter(AILearningEvent.user_id == user_id).first()
        assert event is not None
        profile = session.query(GlobalGenreProfile).filter(GlobalGenreProfile.genre == "trap").first()
        assert profile is not None
        assert profile.metrics.get("feedback_count") == 1


def test_artist_feedback_without_music(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_id, database, headers = _prepare_environment(tmp_path, monkeypatch)

    response = client.post(
        "/feedback/artist",
        json={
            "message": "Quero focar na letra.",
            "mood": "neutral",
            "tags": ["letra"],
            "source": "test",
            "weight": 0.8,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text

    from app.models import ArtistFeedback

    with database.SessionLocal() as session:
        feedback = session.query(ArtistFeedback).filter(ArtistFeedback.user_id == user_id).first()
        assert feedback is not None
        assert feedback.music_asset_id is None


def test_learning_center_crud(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_id, database, headers = _prepare_environment(tmp_path, monkeypatch)

    create_resp = client.post(
        "/learning-centers",
        json={
            "name": "Centro do Trap",
            "scope": "artist",
            "description": "Preferências gerais",
            "is_experimental": True,
            "parameters": {"energy": 0.8},
        },
        headers=headers,
    )
    assert create_resp.status_code == 201, create_resp.text
    center = create_resp.json()
    center_id = center["id"]

    update_resp = client.put(
        f"/learning-centers/{center_id}",
        json={
            "status": "paused",
            "notes": "pausa para ajuste",
            "parameters": {"energy": 0.6},
        },
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "paused"

    delete_resp = client.delete(f"/learning-centers/{center_id}", headers=headers)
    assert delete_resp.status_code == 200
    assert delete_resp.json()["status"] == "archived"

    from app.models import LearningCenter, LearningCenterHistory

    with database.SessionLocal() as session:
        center_row = session.query(LearningCenter).filter(LearningCenter.id == center_id).first()
        assert center_row is not None
        assert center_row.status == "archived"
        history_entries = (
            session.query(LearningCenterHistory)
            .filter(LearningCenterHistory.learning_center_id == center_id)
            .order_by(LearningCenterHistory.version)
            .all()
        )
        assert len(history_entries) == 3
