import io
from importlib import import_module
from pathlib import Path
from typing import List

import pytest

from tests.utils import reset_app_modules, ensure_multipart_stub, install_ai_stubs

try:
	from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover
	pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
	TestClient = _TestClient


def _prepare_client_with_music(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
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
    install_ai_stubs(monkeypatch)

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

	# Fake render function
	import scripts.edit as edit_module

	def fake_adicionar_musica(**kwargs):
		output_path = Path(kwargs["output_path"])
		output_path.parent.mkdir(parents=True, exist_ok=True)
		output_path.write_bytes(b"rendered")
		return str(output_path)

	monkeypatch.setattr(edit_module, "adicionar_musica", fake_adicionar_musica, raising=True)

	# Fake downloader returns a local file
	import app.services.video_pipeline as pipeline_module

	video_file = tmp_path / "video.mp4"
	video_file.write_bytes(b"fake-video-content")

	def fake_downloader(url: str, cookie_file_path: str | None = None, destino: str | None = None):
		return str(video_file)

	monkeypatch.setattr(pipeline_module, "baixar_reel", fake_downloader, raising=True)

	ensure_multipart_stub()
	app_module = import_module("api.app")
	app_module.video_pipeline = pipeline_module.VideoPipeline(downloader=fake_downloader)
	client = TestClient(app_module.app)

	# Register user
	register_resp = client.post(
		"/auth/register",
		json={"email": "artist@example.com", "password": "secret123"},
	)
	assert register_resp.status_code == 201, register_resp.text
	payload = register_resp.json()
	token = payload["access_token"]
	user_id = payload["user"]["id"]
	headers = {"Authorization": f"Bearer {token}"}

	# Create two music assets
	music_service = MusicService(storage_dir=music_store)
	music_ids: List[str] = []
	with database.SessionLocal() as session:
		for idx in range(2):
			audio_bytes = io.BytesIO(b"fake-audio-%d" % idx)
			upload = UploadFile(filename=f"track{idx}.mp3", file=audio_bytes)
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

	return client, user_id, music_ids, headers


def test_feedback_updates_learning_center(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	client, user_id, music_ids, headers = _prepare_client_with_music(tmp_path, monkeypatch)

	# Envia feedback do artista com tags
	resp = client.post(
		"/feedback/artist",
		json={"message": "gostei", "mood": "approved", "tags": ["movimento"], "weight": 1.0},
		headers=headers,
	)
	assert resp.status_code == 201, resp.text

	# Verifica LearningCenter criado e parâmetros
	from app import database
	from app.models import LearningCenter
	with database.SessionLocal() as session:
		center = (
			session.query(LearningCenter)
			.filter(LearningCenter.scope == "artist", LearningCenter.user_id == user_id)
			.first()
		)
		assert center is not None
		assert center.parameters is not None
		profile = center.parameters.get("profile")
		assert profile is not None
		assert profile.get("mood_counts", {}).get("approved", 0) >= 1
		assert profile.get("tag_counts", {}).get("movimento", 0) >= 1


def test_rerank_uses_artist_profile(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
	client, user_id, music_ids, headers = _prepare_client_with_music(tmp_path, monkeypatch)

	# Perfil do artista favorece a tag "movimento" (que aparece nas keywords de fallback)
	resp = client.post(
		"/feedback/artist",
		json={"message": "prefiro cenas de movimento", "tags": ["movimento"], "weight": 1.0},
		headers=headers,
	)
	assert resp.status_code == 201

	# Solicita sugestões
	resp2 = client.post(
		"/videos",
		json={"url": "https://example.com/video", "music_id": music_ids[0]},
		headers=headers,
	)
	assert resp2.status_code == 201, resp2.text
	payload = resp2.json()
	options = payload["options"]
	assert len(options) == 3

	# Os scores devem estar ordenados desc (após rerank) e o topo deve ser > 80.0 (base)
	scores = [opt["score"] for opt in options]
	assert scores == sorted(scores, reverse=True)
	assert any(score > 80.0 for score in scores)
