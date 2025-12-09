from pydantic import BaseModel
from typing import Optional
from app.domain.entities.video_edit import VideoEditStatus


class VideoEditResource(BaseModel):
    """Resource de resposta de vídeo editado"""
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

