from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime


class PublishRequestDTO(BaseModel):
    """DTO para publicação de vídeo"""
    description: str = Field(..., min_length=1, max_length=500)
    videoLink: HttpUrl
    date: datetime

