from pathlib import Path

import pytest

from tests.test_feedback import _prepare_environment
from tests.test_videos import _prepare_video_client
from tests.utils import ensure_multipart_stub

try:
    from fastapi.testclient import TestClient as _TestClient
except RuntimeError as exc:  # pragma: no cover
    pytest.skip(f"fastapi.testclient indisponível: {exc}", allow_module_level=True)
else:
    TestClient = _TestClient


def test_metrics_endpoint_tracks_feedback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_id, database, headers = _prepare_environment(tmp_path, monkeypatch)

    client.post(
        f"/feedback/music/{music_id}",
        json={
            "message": "Feedback de teste para tokens",
            "mood": "positive",
        },
        headers=headers,
    )

    metrics_resp = client.get("/metrics")
    body = metrics_resp.text
    assert "ai_token_usage_total" in body
    assert "http_requests_total" in body


def test_metrics_records_job_duration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    client, user_id, music_ids, headers = _prepare_video_client(tmp_path, monkeypatch)

    response = client.post(
        "/videos",
        json={"url": "https://example.com/video", "music_id": music_ids[0]},
        headers=headers,
    )
    assert response.status_code == 201
    payload = response.json()
    clip_ids = [opt["id"] for opt in payload["options"][:2]]
    video_id = payload.get("video_id") or payload.get("id")

    render_resp = client.post(
        f"/render/{video_id}",
        json={"clip_ids": clip_ids},
        headers=headers,
    )
    assert render_resp.status_code == 200

    metrics_text = client.get("/metrics").text
    assert "video_jobs_total" in metrics_text
