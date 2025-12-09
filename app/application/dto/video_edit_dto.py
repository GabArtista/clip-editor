from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.domain.entities.video_edit import VideoEditStatus


class ApproveVideoEditDTO(BaseModel):
    """DTO para aprovar vídeo editado"""
    video_edit_id: int
    description: str = Field(..., min_length=1, max_length=500, description="Descrição para publicação")


class VideoEditResponseDTO(BaseModel):
    """DTO de resposta de vídeo editado"""
    id: int
    user_id: int
    music_id: int
    s3_url: str
    preview_url: str
    status: VideoEditStatus
    description: Optional[str] = None
    expires_at: Optional[str] = None
    published_at: Optional[str] = None
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

