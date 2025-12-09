from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.infrastructure.database.base import get_db
from app.domain.entities.user import User
from app.application.auth import get_current_user
from app.application.dto.publish_dto import PublishRequestDTO
from app.infrastructure.external import N8NClient

router = APIRouter(prefix="/api/v1/publish", tags=["Publish"])


@router.post("", status_code=status.HTTP_200_OK)
async def publish_video(
    publish_data: PublishRequestDTO,
    current_user: User = Depends(get_current_user)
):
    """Publica vídeo via webhook N8N"""
    try:
        n8n_client = N8NClient()
        
        # Converte datetime para string ISO
        date_str = publish_data.date.isoformat() + "Z" if publish_data.date.tzinfo is None else publish_data.date.isoformat()
        
        result = await n8n_client.publish_video(
            description=publish_data.description,
            video_link=str(publish_data.videoLink),
            date=date_str
        )
        
        return {
            "success": True,
            "message": "Vídeo publicado com sucesso",
            "data": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao publicar vídeo: {str(e)}"
        )

