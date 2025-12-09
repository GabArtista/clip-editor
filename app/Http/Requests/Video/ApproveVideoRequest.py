from pydantic import BaseModel, Field


class ApproveVideoRequest(BaseModel):
    """Request para aprovar vídeo editado"""
    video_edit_id: int
    description: str = Field(..., min_length=1, max_length=500, description="Descrição para publicação")

