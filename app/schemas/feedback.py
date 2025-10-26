from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MusicFeedbackRequest(BaseModel):
    message: str
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    weight: Optional[float] = None


class ArtistFeedbackRequest(BaseModel):
    message: str
    mood: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    weight: Optional[float] = None
    music_id: Optional[str] = Field(None, alias="music_asset_id")

    class Config:
        populate_by_name = True


class FeedbackResponse(BaseModel):
    id: str
    created_at: datetime


class LearningCenterCreateRequest(BaseModel):
    name: str
    scope: str
    music_asset_id: Optional[str] = None
    genre: Optional[str] = None
    description: Optional[str] = None
    is_experimental: bool = False
    parameters: Optional[dict] = None


class LearningCenterUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_experimental: Optional[bool] = None
    parameters: Optional[dict] = None
    notes: Optional[str] = None


class LearningCenterResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    scope: str
    status: str
    user_id: Optional[str]
    music_asset_id: Optional[str]
    genre: Optional[str]
    is_experimental: bool
    version: int
    parameters: Optional[dict]
    baseline_snapshot: Optional[dict]
    created_at: datetime
    updated_at: datetime


class LearningCenterHistoryEntry(BaseModel):
    version: int
    status: str
    created_at: datetime
    notes: Optional[str]
    payload: Optional[dict]
