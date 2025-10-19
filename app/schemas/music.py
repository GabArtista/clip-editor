from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MusicBeatSchema(BaseModel):
    timestamp_seconds: float
    beat_type: str
    confidence: Optional[float] = None


class MusicEmbeddingSchema(BaseModel):
    embedding_type: str
    vector: dict


class MusicTranscriptionSchema(BaseModel):
    transcript_text: Optional[str]
    language: str
    model_version: Optional[str] = None
    confidence: Optional[float] = None


class MusicUploadResponse(BaseModel):
    music_id: str = Field(..., alias="id")
    title: str
    status: str
    genre: Optional[str] = None
    genre_inferred: Optional[str] = None
    bpm: Optional[int] = None
    musical_key: Optional[str] = None
    analysis_version: Optional[str] = None
    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        populate_by_name = True


class MusicDetailResponse(MusicUploadResponse):
    description: Optional[str] = None
    genre_confidence: Optional[float] = None
    analysis_summary: Optional[dict] = None
    beats: List[MusicBeatSchema]
    embeddings: List[MusicEmbeddingSchema]
    transcription: Optional[MusicTranscriptionSchema]
