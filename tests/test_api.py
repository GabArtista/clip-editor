from __future__ import annotations

import io
import time


def register_and_login(client, email: str = "artist@example.com"):
    payload = {
        "email": email,
        "password": "StrongerPassword123",
        "display_name": "Artist",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    return headers, data["user"]["id"]


def deposit(client, headers, amount: str = "20.00"):
    response = client.post("/wallet/deposit", json={"amount": amount}, headers=headers)
    assert response.status_code == 200
    return response.json()


def upload_music(client, headers, title="Minha Música"):
    file_content = io.BytesIO(b"fake-mp3-data")
    files = {"audio_file": ("track.mp3", file_content, "audio/mpeg")}
    data = {
        "title": title,
        "description": "faixa teste",
        "duration_seconds": "120",
        "bpm": "120",
    }
    response = client.post("/music", data=data, files=files, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_register_and_wallet_flow(client):
    headers, _ = register_and_login(client, "wallet@example.com")
    balance = deposit(client, headers, "15.50")
    assert balance["balance"] == "15.50"
    tx_response = client.get("/wallet/transactions", headers=headers)
    assert tx_response.status_code == 200
    transactions = tx_response.json()
    assert len(transactions) == 1
    assert transactions[0]["transaction_type"] == "deposit"


def test_music_transcription_flow(client):
    headers, _ = register_and_login(client, "music@example.com")
    deposit(client, headers, "25.00")
    music_id = upload_music(client, headers, "Faixa Viral")
    response = client.post(f"/music/{music_id}/transcribe", json={"language": "pt"}, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["music_id"] == music_id
    assert data["transcript_text"] is not None
    detail = client.get(f"/music/{music_id}", headers=headers).json()
    assert detail["has_transcription"] is True
    assert detail["transcript_text"] == data["transcript_text"]


def test_video_suggestions_and_variations(client):
    start = time.time()
    headers, _ = register_and_login(client, "video@example.com")
    deposit(client, headers, "40.00")
    music_id = upload_music(client, headers, "Impacto")
    client.post(f"/music/{music_id}/transcribe", json={"language": "pt"}, headers=headers)

    suggestions = client.post(
        "/videos/suggestions",
        json={
            "video_url": "https://example.com/video.mp4",
            "video_duration_seconds": 90,
            "notes": "Quero viralizar no TikTok",
            "music_ids": [music_id],
        },
        headers=headers,
    )
    assert suggestions.status_code == 200, suggestions.text
    suggestion_items = suggestions.json()["items"]
    assert len(suggestion_items) == 3

    variations = client.post(
        "/videos/variations",
        json={
            "video_url": "https://example.com/video.mp4",
            "video_duration_seconds": 90,
            "notes": "Versão final",
            "music_id": music_id,
        },
        headers=headers,
    )
    assert variations.status_code == 200, variations.text
    variation_items = variations.json()["items"]
    assert len(variation_items) == 3
    assert "segments" in variation_items[0]
