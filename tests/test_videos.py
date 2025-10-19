import io
import sys
from importlib import import_module
from pathlib import Path
from typing import List

import pytest

from tests.utils import reset_app_modules, ensure_multipart_stub

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover - ambiente sem httpx
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def _prepare_video_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    from app.models import Base, User
    from app.services.music_service import MusicMetadata, MusicService
    from starlette.datastructures import UploadFile

    Base.metadata.create_all(database.engine)

    music_service = MusicService(storage_dir=music_store)
    with database.SessionLocal() as session:
        user = User(email="artist@example.com")
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id

        music_ids: List[str] = []
        for idx in range(2):
            audio_bytes = io.BytesIO(b"fake-audio-%d" % idx)
            upload = UploadFile(
                filename=f"track{idx}.mp3",
                file=audio_bytes,
            )
            asset = music_service.create_music_asset(
                session,
                upload,
                MusicMetadata(
                    user_id=user_id,
                    title=f"Track {idx}",
                    declared_genre="trap" if idx == 0 else "boom bap",
                    description="demo",
                ),
            )
            music_ids.append(asset.id)

    video_file = tmp_path / "video.mp4"
    video_file.write_bytes(b"fake-video-content")

    import scripts.edit as edit_module

    def fake_adicionar_musica(**kwargs):
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"rendered")
        return str(output_path)

    monkeypatch.setattr(edit_module, "adicionar_musica", fake_adicionar_musica, raising=True)

    import app.services.video_pipeline as pipeline_module

    def fake_downloader(url: str, cookie_file_path: str | None = None, destino: str | None = None):
        return str(video_file)

    monkeypatch.setattr(pipeline_module, "baixar_reel", fake_downloader, raising=True)

    job_tasks = import_module("jobs.tasks")
    monkeypatch.setattr(job_tasks, "adicionar_musica", fake_adicionar_musica, raising=True)

    import_module("jobs.manager")

    ensure_multipart_stub()
    app_module = import_module("api.app")

    app_module.video_pipeline = pipeline_module.VideoPipeline(downloader=fake_downloader)
    client = TestClient(app_module.app)
    return client, user_id, music_ids


def _min_difference(offsets: List[float]) -> float:
    if len(offsets) < 2:
        return 0.0
    sorted_offsets = sorted(offsets)
    return min(b - a for a, b in zip(sorted_offsets, sorted_offsets[1:]))


def test_video_submission_with_specific_music(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_ids = _prepare_video_client(tmp_path, monkeypatch)

    response = client.post(
        "/videos",
        json={"user_id": user_id, "url": "https://example.com/video", "music_id": music_ids[0]},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["status"] == "ready"
    assert len(payload["options"]) == 3

    offsets = [opt["music_start_seconds"] for opt in payload["options"]]
    assert _min_difference([offset for offset in offsets if offset is not None]) >= 5.0

    video_id = payload.get("video_id") or payload.get("id")
    assert video_id
    from app import database
    from app.models import VideoIngest

    with database.SessionLocal() as session:
        ingest = (
            session.query(VideoIngest)
            .filter(VideoIngest.id == video_id)
            .first()
        )
        assert ingest is not None
        assert len(ingest.clip_models) == 3
        assert ingest.analysis is not None


def test_video_submission_without_specific_music(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_ids = _prepare_video_client(tmp_path, monkeypatch)

    response = client.post(
        "/videos",
        json={"user_id": user_id, "url": "https://example.com/video"},
    )
    assert response.status_code == 201
    payload = response.json()
    assert len(payload["options"]) >= 4  # 2 variações para cada música criada

    # agrupa por música para verificar diversidade
    offsets_by_music = {}
    for opt in payload["options"]:
        offsets_by_music.setdefault(opt["music_asset_id"], []).append(opt["music_start_seconds"])
    for offsets in offsets_by_music.values():
        numeric_offsets = [offset for offset in offsets if offset is not None]
        if len(numeric_offsets) >= 2:
            assert _min_difference(numeric_offsets) >= 5.0


def test_render_variants_job(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_ids = _prepare_video_client(tmp_path, monkeypatch)

    response = client.post(
        "/videos",
        json={"user_id": user_id, "url": "https://example.com/video", "music_id": music_ids[0]},
    )
    assert response.status_code == 201
    payload = response.json()
    video_id = payload.get("video_id") or payload.get("id")
    assert video_id
    clip_ids = [opt["id"] for opt in payload["options"][:2]]

    from jobs.manager import JobManager

    job_manager = JobManager()
    job_id = job_manager.enqueue_video_edit(
        {
            "mode": "clip_render",
            "video_ingest_id": video_id,
            "clip_ids": clip_ids,
        }
    )
    job_data = job_manager.get_job(job_id)
    assert job_data is not None
    assert job_data["status"] == "done"
    assert len(job_data["result"]["outputs"]) == 2
