from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MusicResource(BaseModel):
    """Resource de resposta de música"""
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

