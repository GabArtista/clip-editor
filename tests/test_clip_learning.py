import io
from uuid import UUID

import pytest

from tests.utils import ensure_multipart_stub, install_ai_stubs, reset_app_modules

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def _prepare_environment(tmp_path, monkeypatch):
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
    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")

    reset_app_modules()

    from importlib import import_module

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

    Base.metadata.create_all(database.engine)

    import scripts.edit as edit_module

    def fake_adicionar_musica(**kwargs):
        output_path = processed_dir / "fake_render.mp4"
        output_path.write_bytes(b"rendered")
        return str(output_path)

    monkeypatch.setattr(edit_module, "adicionar_musica", fake_adicionar_musica, raising=True)

    import app.services.video_pipeline as pipeline_module

    video_file = tmp_path / "video.mp4"
    video_file.write_bytes(b"fake-video-content")

    def fake_downloader(url: str, cookie_file_path: str | None = None, destino: str | None = None):
        return str(video_file)

    monkeypatch.setattr(pipeline_module, "baixar_reel", fake_downloader, raising=True)

    install_ai_stubs(monkeypatch)
    ensure_multipart_stub()

    app_module = import_module("api.app")
    app_module.video_pipeline = pipeline_module.VideoPipeline(downloader=fake_downloader)
    client = TestClient(app_module.app)

    return client


def _register_user_and_music(client):
    register_resp = client.post(
        "/auth/register",
        json={"email": "learner@example.com", "password": "secret123"},
    )
    assert register_resp.status_code == 201, register_resp.text
    payload = register_resp.json()
    token = payload["access_token"]
    user_id = payload["user"]["id"]
    headers = {"Authorization": f"Bearer {token}"}

    from app import database
    from app.services.music_service import MusicMetadata, MusicService
    from starlette.datastructures import UploadFile

    with database.SessionLocal() as session:
        music_service = MusicService()
        audio_bytes = io.BytesIO(b"fake-audio")
        upload = UploadFile(filename="track.mp3", file=audio_bytes)
        asset = music_service.create_music_asset(
            session,
            upload,
            MusicMetadata(user_id=user_id, title="Track", declared_genre="trap"),
        )
    return headers, user_id, asset.id


def test_learning_train_endpoint_builds_model(tmp_path, monkeypatch):
    client = _prepare_environment(tmp_path, monkeypatch)
    headers, user_id, music_id = _register_user_and_music(client)
    user_uuid = UUID(user_id)

    resp = client.post(
        "/videos",
        json={"url": "https://example.com/video", "music_id": str(music_id)},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    options = resp.json()["options"]
    assert len(options) >= 2

    clip_ids = [UUID(opt["id"]) for opt in options[:2]]

    from app import database
    from app.models import ClipFeedback, LearningCenter, VideoClipModel, VideoIngest
    from app.services.learning import ClipLearningService

    with database.SessionLocal() as session:
        clips = (
            session.query(VideoClipModel)
            .filter(VideoClipModel.id.in_(clip_ids))
            .order_by(VideoClipModel.option_order)
            .all()
        )
        assert len(clips) == 2

        short_segments = list(clips[0].video_segments or [])
        short_segments[0]["video_end_seconds"] = short_segments[0]["video_start_seconds"] + 6.0
        clips[0].video_segments = short_segments
        clips[0].score = 60.0

        long_segments = list(clips[1].video_segments or [])
        long_segments[0]["video_end_seconds"] = long_segments[0]["video_start_seconds"] + 15.0
        clips[1].video_segments = long_segments
        clips[1].score = 50.0

        session.add_all(clips)

        session.add(
            ClipFeedback(
                clip_id=clips[0].id,
                user_id=user_uuid,
                mood="negative",
                message="quero cortes mais longos",
            )
        )
        session.add(
            ClipFeedback(
                clip_id=clips[1].id,
                user_id=user_uuid,
                mood="positive",
                message="perfeito",
            )
        )
        session.commit()

    train_resp = client.post("/learning/train", headers=headers)
    assert train_resp.status_code == 200, train_resp.text
    payload = train_resp.json()
    assert payload["message"] == "trained"
    assert payload["result"]["samples"] == 2
    assert payload["result"]["positives"] == 1

    with database.SessionLocal() as session:
        center = (
            session.query(LearningCenter)
            .filter(LearningCenter.scope == "artist", LearningCenter.user_id == user_uuid)
            .first()
        )
        assert center is not None
        model_payload = (center.parameters or {}).get("learned_model")
        assert model_payload is not None

        service = ClipLearningService()

        ingest = session.query(VideoIngest).filter(VideoIngest.user_id == user_uuid).first()
        assert ingest is not None and ingest.analysis is not None

        clip_short = session.get(VideoClipModel, clip_ids[0])
        clip_long = session.get(VideoClipModel, clip_ids[1])
        long_score = service.predict_score(
            model_payload,
            service.build_features_for_clip(clip_long, ingest.analysis, clip_long.music_asset, ingest),
        )
        short_score = service.predict_score(
            model_payload,
            service.build_features_for_clip(clip_short, ingest.analysis, clip_short.music_asset, ingest),
        )
        assert long_score > short_score
