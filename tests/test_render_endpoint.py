from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import BaseModel

from tests.utils import reset_app_modules


class DummyRenderRequest(BaseModel):
    clip_ids: list[str]
    return_format: str = "url"


def _setup_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    db_path = runtime_dir / "app.db"
    monkeypatch.setenv("RUNTIME_BASE_DIR", str(runtime_dir))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("FAKE_REDIS", "1")
    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")

    reset_app_modules()

    from importlib import import_module

    import_module("app.database")
    from app import database
    from app.models import Base

    Base.metadata.create_all(database.engine)
    return database


def test_render_allows_clip_from_same_video(tmp_path, monkeypatch: pytest.MonkeyPatch):
    database = _setup_db(tmp_path, monkeypatch)

    from app.models import AssetStatus, User, VideoClipModel, VideoIngest
    import api.app as app_module

    with database.SessionLocal() as session:
        user = User(email="render@example.com", password_hash="hash")
        session.add(user)
        session.flush()

        video_id = uuid.uuid4()
        clip_id = uuid.uuid4()

        ingest = VideoIngest(
            id=video_id,
            user_id=user.id,
            source_url="https://example.com/video",
            status=AssetStatus.ready,
            duration_seconds=30.0,
            created_at=datetime.now(timezone.utc),
        )
        session.add(ingest)
        session.flush()

        clip = VideoClipModel(
            id=clip_id,
            video_ingest_id=ingest.id,
            music_asset_id=None,
            option_order=1,
            variant_label="Clip",
            description="clip",
            video_segments=[{"start": 0.0, "end": 10.0}],
            music_start_seconds=0.0,
            music_end_seconds=10.0,
            diversity_tags=["auto"],
            score=75.0,
        )
        session.add(clip)
        session.commit()

        called_payload = {}

        job_data = {
            "job_id": "job-123",
            "status": "queued",
            "request": {},
        }

        def fake_enqueue(payload):
            called_payload.update(payload)
            job_data["request"] = payload.copy()
            return job_data["job_id"]

        def fake_get_job(job_id):
            if job_id == job_data["job_id"]:
                return job_data
            return None

        monkeypatch.setattr(app_module.job_manager, "enqueue_video_edit", fake_enqueue)
        monkeypatch.setattr(app_module.job_manager, "get_job", fake_get_job)

        response = app_module.render_video_variants(
            video_id=str(video_id),
            data=DummyRenderRequest(clip_ids=[str(clip_id)]),
            db=session,
            current_user=user,
        )

    assert response["ok"] is True
    assert called_payload["video_ingest_id"] == str(video_id)
    assert called_payload["clip_ids"] == [str(clip_id)]

    job_info = app_module.get_job_status(response["job_id"], current_user=user)
    assert job_info["request"]["user_id"] == str(user.id)


def test_render_rejects_clip_from_other_video(tmp_path, monkeypatch: pytest.MonkeyPatch):
    database = _setup_db(tmp_path, monkeypatch)

    from app.models import AssetStatus, User, VideoClipModel, VideoIngest
    import api.app as app_module
    from fastapi import HTTPException

    with database.SessionLocal() as session:
        user = User(email="render2@example.com", password_hash="hash")
        session.add(user)
        session.flush()

        video_one = uuid.uuid4()
        video_two = uuid.uuid4()

        ingest_one = VideoIngest(
            id=video_one,
            user_id=user.id,
            source_url="https://example.com/video1",
            status=AssetStatus.ready,
            duration_seconds=30.0,
            created_at=datetime.now(timezone.utc),
        )
        ingest_two = VideoIngest(
            id=video_two,
            user_id=user.id,
            source_url="https://example.com/video2",
            status=AssetStatus.ready,
            duration_seconds=30.0,
            created_at=datetime.now(timezone.utc),
        )
        session.add_all([ingest_one, ingest_two])
        session.flush()

        clip_other = VideoClipModel(
            id=uuid.uuid4(),
            video_ingest_id=ingest_two.id,
            music_asset_id=None,
            option_order=1,
            variant_label="Clip",
            description="clip",
            video_segments=[{"start": 0.0, "end": 10.0}],
            music_start_seconds=0.0,
            music_end_seconds=10.0,
            diversity_tags=["auto"],
            score=70.0,
        )
        session.add(clip_other)
        session.commit()

        with pytest.raises(HTTPException) as exc:
            app_module.render_video_variants(
                video_id=str(video_one),
                data=DummyRenderRequest(clip_ids=[str(clip_other.id)]),
                db=session,
                current_user=user,
            )

    assert exc.value.status_code == 400
    assert "Clipes não pertencem a este vídeo" in exc.value.detail
