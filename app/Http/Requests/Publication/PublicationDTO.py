from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl
from app.domain.entities.publication_queue import PublicationStatus


class PublicationQueueCreateDTO(BaseModel):
    """Payload para criação de publicação na fila."""

    video_url: HttpUrl | str = Field(..., description="URL pública do vídeo (ex: S3)")
    description: str = Field(..., min_length=1, max_length=500, description="Descrição da publicação")


class PublicationQueueResponseDTO(BaseModel):
    """Resposta padronizada da fila de publicações."""

    id: int
    user_id: int
    video_path: Optional[str] = None
    video_url: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    status: PublicationStatus
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


