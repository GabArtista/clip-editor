from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MusicCreateDTO(BaseModel):
    """DTO para criação de música"""
    name: str = Field(..., min_length=1, max_length=255)


class MusicUpdateDTO(BaseModel):
    """DTO para atualização de música"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)


class MusicResponseDTO(BaseModel):
    """DTO de resposta de música"""
    id: int
    user_id: int
    name: str
    filename: str
    file_path: str
    duration: Optional[float] = None
    file_size: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

