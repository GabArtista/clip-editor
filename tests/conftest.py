import os
import shutil
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_db.sqlite3")
os.environ.setdefault("MUSIC_STORAGE_DIR", "runtime/test_music_storage")
os.environ.setdefault("VIDEOS_DIR", "runtime/test_videos")
os.environ.setdefault("PROCESSED_DIR", "runtime/test_processed")

from api.app import app  # noqa: E402
from app.database import Base, engine  # noqa: E402


def _reset_storage():
    for env_var in ("MUSIC_STORAGE_DIR", "VIDEOS_DIR", "PROCESSED_DIR"):
        path = os.getenv(env_var)
        if path and os.path.exists(path):
            shutil.rmtree(path)


@pytest.fixture(autouse=True)
def _clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    _reset_storage()
    yield
    Base.metadata.drop_all(bind=engine)
    _reset_storage()


@pytest.fixture
def client():
    return TestClient(app)
