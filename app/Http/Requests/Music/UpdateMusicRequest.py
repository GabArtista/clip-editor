from pydantic import BaseModel, Field
from typing import Optional


class UpdateMusicRequest(BaseModel):
    """Request para atualização de música"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)

