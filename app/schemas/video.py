from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, HttpUrl


class VideoSuggestionRequest(BaseModel):
    video_url: HttpUrl
    video_duration_seconds: float = Field(gt=5)
    notes: Optional[str] = Field(default=None, max_length=512)
    music_ids: Optional[List[str]] = None


class VideoSuggestionItem(BaseModel):
    suggestion_id: str
    music_id: str
    start_time_seconds: float
    end_time_seconds: float
    reasoning: str
    prompt: str


class VideoSuggestionResponse(BaseModel):
    items: List[VideoSuggestionItem]


class VideoVariationRequest(BaseModel):
    video_url: HttpUrl
    video_duration_seconds: float = Field(gt=5)
    notes: Optional[str] = Field(default=None, max_length=512)
    music_id: str


class VideoVariationSegment(BaseModel):
    label: str
    video_start: float
    video_end: float
    music_offset: float


class VideoVariationItem(BaseModel):
    variation_id: str
    music_id: str
    description: str
    segments: List[VideoVariationSegment]


class VideoVariationResponse(BaseModel):
    items: List[VideoVariationItem]
