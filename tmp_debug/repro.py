import io
from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from tests.utils import ensure_multipart_stub, install_ai_stubs, reset_app_modules


def prepare(tmp_path):
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    music_store = tmp_path / "music_store"
    videos_dir = tmp_path / "videos"
    processed_dir = tmp_path / "processed"
    videos_dir.mkdir(exist_ok=True)
    processed_dir.mkdir(exist_ok=True)

    db_path = runtime_dir / "app.db"

    import os
    from importlib import import_module

    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
    os.environ["MUSIC_STORAGE_DIR"] = str(music_store)
    os.environ["VIDEOS_DIR"] = str(videos_dir)
    os.environ["PROCESSED_DIR"] = str(processed_dir)
    os.environ["JOB_EXECUTION_MODE"] = "sync"

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

    Base.metadata.create_all(database.engine)

    import scripts.edit as edit_module

    def fake_adicionar_musica(**kwargs):
        output_path = processed_dir / "fake_render.mp4"
        output_path.write_bytes(b"rendered")
        return str(output_path)

    edit_module.adicionar_musica = fake_adicionar_musica

    import app.services.video_pipeline as pipeline_module

    video_file = tmp_path / "video.mp4"
    video_file.write_bytes(b"fake-video-content")

    def fake_downloader(url: str, cookie_file_path: str | None = None, destino: str | None = None):
        return str(video_file)

    pipeline_module.baixar_reel = fake_downloader

    install_ai_stubs(type("MP", (), {"setattr": staticmethod(lambda obj, name, value, raising=True: None)})())
    ensure_multipart_stub()

    app_module = import_module("api.app")
    app_module.video_pipeline = pipeline_module.VideoPipeline(downloader=fake_downloader)
    client = TestClient(app_module.app)
    return client


def main():
    tmp = Path("tmp_debug/repro_env")
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    client = prepare(tmp)

    resp = client.post("/auth/register", json={"email": "learner@example.com", "password": "secret123"})
    print("register", resp.status_code)
    headers = {"Authorization": f"Bearer {resp.json()['access_token']}"}

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
            MusicMetadata(user_id=resp.json()["user"]["id"], title="Track", declared_genre="trap"),
        )
    music_id = asset.id

    resp2 = client.post("/videos", json={"url": "https://example.com/video", "music_id": str(music_id)}, headers=headers)
    print("videos", resp2.status_code)
    print(resp2.json())


if __name__ == "__main__":
    main()
