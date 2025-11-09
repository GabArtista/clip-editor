from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MusicUploadResponse(BaseModel):
    id: str
    title: str
    duration_seconds: float | None
    bpm: int | None
    created_at: datetime


class MusicListItem(MusicUploadResponse):
    description: str | None = None
    has_transcription: bool = False


class MusicDetailResponse(MusicListItem):
    transcript_text: str | None = None
    language: str | None = None


class MusicTranscriptionRequest(BaseModel):
    language: str = Field(default="pt", min_length=2, max_length=8)


class MusicTranscriptionResponse(BaseModel):
    id: str
    music_id: str
    language: str
    transcript_text: str | None
    confidence: float | None
    generated_by: str | None
    created_at: datetime
