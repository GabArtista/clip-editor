from pydantic import BaseModel, Field


class CreateMusicRequest(BaseModel):
    """Request para criação de música"""
    name: str = Field(..., min_length=1, max_length=255)

