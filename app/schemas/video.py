from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VideoClipOption(BaseModel):
    id: str
    option_order: int
    variant_label: str
    description: Optional[str]
    music_asset_id: Optional[str]
    video_segments: List[dict]
    music_start_seconds: Optional[float]
    music_end_seconds: Optional[float]
    diversity_tags: Optional[List[str]]
    score: Optional[float]


class VideoSubmissionResponse(BaseModel):
    video_id: str = Field(..., alias="id")
    status: str
    duration_seconds: Optional[float]
    options: List[VideoClipOption]

    class Config:
        populate_by_name = True


class VideoListItem(VideoSubmissionResponse):
    source_url: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class VideoDetailResponse(VideoListItem):
    analysis: Optional[dict]
