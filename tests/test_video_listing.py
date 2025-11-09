from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from tests.utils import reset_app_modules, install_ai_stubs


def _setup_environment(tmp_path, monkeypatch: pytest.MonkeyPatch):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    db_path = runtime_dir / "app.db"

    monkeypatch.setenv("RUNTIME_BASE_DIR", str(runtime_dir))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("FAKE_REDIS", "1")
    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")

    reset_app_modules()
    install_ai_stubs(monkeypatch)

    from importlib import import_module

    import_module("app.database")
    from app import database
    from app.models import Base

    Base.metadata.create_all(database.engine)

    return database


def test_list_videos_returns_user_ingests(tmp_path, monkeypatch: pytest.MonkeyPatch):
    database = _setup_environment(tmp_path, monkeypatch)

    from app.models import AssetStatus, User, VideoClipModel, VideoIngest
    from api.app import list_videos

    now = datetime.now(timezone.utc)
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()

    with database.SessionLocal() as session:
        user = User(email="list-user@example.com", password_hash="hash")
        session.add(user)
        session.commit()
        session.refresh(user)

        first_ingest = VideoIngest(
            id=first_id,
            user_id=user.id,
            source_url="https://example.com/video-one",
            status=AssetStatus.ready,
            duration_seconds=45.0,
            created_at=now - timedelta(minutes=5),
            updated_at=now - timedelta(minutes=4),
        )
        second_ingest = VideoIngest(
            id=second_id,
            user_id=user.id,
            source_url="https://example.com/video-two",
            status=AssetStatus.ready,
            duration_seconds=60.0,
            created_at=now,
            updated_at=now + timedelta(minutes=1),
        )

        session.add_all([first_ingest, second_ingest])
        session.flush()

        clip_one = VideoClipModel(
            video_ingest_id=first_ingest.id,
            music_asset_id=None,
            option_order=1,
            variant_label="First clip",
            description="clip",
            video_segments=[{"start": 0.0, "end": 10.0}],
            music_start_seconds=0.0,
            music_end_seconds=10.0,
            diversity_tags=["auto"],
            score=80.0,
        )
        clip_two = VideoClipModel(
            video_ingest_id=second_ingest.id,
            music_asset_id=None,
            option_order=1,
            variant_label="Second clip",
            description="clip",
            video_segments=[{"start": 5.0, "end": 15.0}],
            music_start_seconds=5.0,
            music_end_seconds=15.0,
            diversity_tags=["auto"],
            score=82.0,
        )
        session.add_all([clip_one, clip_two])
        session.commit()

        result = list_videos(db=session, current_user=user)

    assert [item["id"] for item in result] == [str(second_id), str(first_id)]
    for item in result:
        assert "source_url" in item and item["source_url"]
        assert isinstance(item["options"], list) and item["options"]
        assert "created_at" in item
        assert "updated_at" in item
