from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.domain.entities.publication_queue import PublicationStatus


class PublicationQueueResponseDTO(BaseModel):
    """DTO de resposta de publicação na fila"""
    id: int
    user_id: int
    video_path: str
    video_url: str
    description: str
    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    status: PublicationStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PublicationQueueCreateDTO(BaseModel):
    """DTO para criar publicação na fila"""
    video_url: str = Field(..., description="URL do vídeo processado")
    description: str = Field(..., min_length=1, max_length=500, description="Descrição do vídeo")

