import os
import sys
import time
from importlib import import_module
from pathlib import Path

import pytest

from tests.utils import reset_app_modules, ensure_multipart_stub

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # falta httpx (p.ex. ambiente sem rede)
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def _build_test_client(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    rate_limit_requests: int = 5,
) -> TestClient:
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(project_root))
    monkeypatch.chdir(tmp_path)

    runtime_dir = tmp_path / "runtime"
    music_dir = tmp_path / "music"
    videos_dir = tmp_path / "videos"
    processed_dir = tmp_path / "processed"
    cookies_dir = tmp_path / "cookies"

    for directory in (music_dir, videos_dir, processed_dir, cookies_dir):
        directory.mkdir(parents=True, exist_ok=True)

    session_file = cookies_dir / "session.netscape"
    session_file.write_text("# dummy cookie\n", encoding="utf-8")

    (music_dir / "Fala.mp3").write_text("fake-mp3", encoding="utf-8")

    monkeypatch.setenv("JOB_EXECUTION_MODE", "sync")
    monkeypatch.setenv("FAKE_REDIS", "1")
    monkeypatch.setenv("RUNTIME_BASE_DIR", str(runtime_dir))
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", str(rate_limit_requests))
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
    monkeypatch.setenv("JOB_CLEANUP_TTL_SECONDS", "999999")
    monkeypatch.setenv("JOB_CLEANUP_INTERVAL_SECONDS", "999999")

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
    import_module("jobs.config")
    import_module("jobs.state")
    import_module("jobs.cleanup")
    import_module("jobs.tasks")
    import_module("jobs.manager")

    # Patch paths inside jobs.tasks to apontar para tmp_path.
    import jobs.tasks as tasks_module

    monkeypatch.setattr(tasks_module, "SESSION_FILE_PATH", session_file)
    monkeypatch.setattr(tasks_module, "VIDEOS_DIR", videos_dir)
    monkeypatch.setattr(tasks_module, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(tasks_module, "MUSIC_DIR", music_dir)

    # Stubs para download/renderização.
    def fake_download(url: str, cookie_file_path: str | None = None, destino: str = "videos/") -> str:
        fake_input = videos_dir / "input.mp4"
        fake_input.write_text("video-bytes", encoding="utf-8")
        return str(fake_input)

    def fake_edit(**kwargs):
        output_path = Path(kwargs["output_path"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("rendered", encoding="utf-8")
        return str(output_path)

    import scripts.download as download_module
    import scripts.edit as edit_module

    monkeypatch.setattr(download_module, "baixar_reel", fake_download)
    monkeypatch.setattr(edit_module, "adicionar_musica", fake_edit)
    monkeypatch.setattr(tasks_module, "baixar_reel", fake_download)
    monkeypatch.setattr(tasks_module, "adicionar_musica", fake_edit)
    assert tasks_module.baixar_reel is fake_download

    ensure_multipart_stub()
    app_module = import_module("api.app")
    return TestClient(app_module.app)


def test_process_job_sync_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client = _build_test_client(tmp_path, monkeypatch)

    payload = {
        "url": "https://example.com/video",
        "music": "Fala",
        "impact_music": 10.0,
        "impact_video": 3.0,
        "return_format": "url",
    }

    response = client.post("/processar", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    job_id = data["job_id"]

    status_response = client.get(f"/jobs/{job_id}")
    assert status_response.status_code == 200
    job_data = status_response.json()
    assert job_data["status"] == "done"
    assert job_data["result"]["video_url"].startswith("/videos/")
    assert job_data["result"]["filename"].endswith("_Fala.mp4")


def test_rate_limit_blocks_excess(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client = _build_test_client(tmp_path, monkeypatch, rate_limit_requests=1)

    payload = {
        "url": "https://example.com/video",
        "music": "Fala",
        "impact_music": 12.0,
        "impact_video": 5.0,
        "return_format": "url",
    }

    first = client.post("/processar", json=payload)
    assert first.status_code == 200

    second = client.post("/processar", json=payload)
    assert second.status_code == 429
    assert "Limite de processamento" in second.json()["detail"]


def test_cleanup_directory_removes_old_files(tmp_path: Path):
    from jobs.cleanup import cleanup_directory

    old_file = tmp_path / "to_delete.mp4"
    old_file.write_text("x", encoding="utf-8")
    old_timestamp = time.time() - 7200
    os.utime(old_file, (old_timestamp, old_timestamp))

    removed = cleanup_directory(tmp_path, older_than_seconds=3600)
    assert str(old_file) in removed
    assert not old_file.exists()
