from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.infrastructure.database.base import get_db
from app.infrastructure.repositories import PublicationQueueRepository, UserRepository
from app.domain.services.publication_service import PublicationService
from app.domain.services.publication_scheduler_service import PublicationSchedulerService
from app.domain.entities.user import User
from app.application.auth import get_current_user
from app.application.dto.publication_dto import (
    PublicationQueueResponseDTO,
    PublicationQueueCreateDTO
)

router = APIRouter(prefix="/api/v1/publications", tags=["Publications"])


@router.post("", response_model=PublicationQueueResponseDTO, status_code=status.HTTP_201_CREATED)
def queue_publication(
    publication_data: PublicationQueueCreateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Adiciona publicação na fila"""
    try:
        # Verifica se usuário tem webhook configurado
        if not current_user.webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook não configurado. Configure seu webhook URL no perfil."
            )
        
        # Valida URL do vídeo (pode ser S3 ou local)
        # Se for URL S3, não precisa validar arquivo local
        video_path = publication_data.video_url  # Para S3, path = url
        video_url = publication_data.video_url
        
        # Se for URL local, valida arquivo
        if not video_url.startswith("http"):
            import os
            from app.config import settings
            video_filename = video_url.split("/")[-1]
            video_path = os.path.join(settings.PROCESSED_DIR, str(current_user.id), video_filename)
            
            if not os.path.exists(video_path):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Vídeo não encontrado"
                )
        
        # Cria publicação na fila
        publication_repo = PublicationQueueRepository(db)
        scheduler_service = PublicationSchedulerService(publication_repo)
        publication_service = PublicationService(publication_repo, scheduler_service)
        
        publication = publication_service.queue_publication(
            user_id=current_user.id,
            video_path=video_path,
            video_url=publication_data.video_url,
            description=publication_data.description
        )
        
        return PublicationQueueResponseDTO(
            id=publication.id,
            user_id=publication.user_id,
            video_path=publication.video_path,
            video_url=publication.video_url,
            description=publication.description,
            scheduled_date=publication.scheduled_date,
            published_date=publication.published_date,
            status=publication.status,
            error_message=publication.error_message,
            created_at=publication.created_at,
            updated_at=publication.updated_at
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao adicionar publicação na fila: {str(e)}"
        )


@router.get("", response_model=List[PublicationQueueResponseDTO])
def list_publications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista publicações do usuário"""
    try:
        publication_repo = PublicationQueueRepository(db)
        scheduler_service = PublicationSchedulerService(publication_repo)
        publication_service = PublicationService(publication_repo, scheduler_service)
        
        publications = publication_service.get_user_queue(current_user.id, skip=skip, limit=limit)
        
        return [
            PublicationQueueResponseDTO(
                id=pub.id,
                user_id=pub.user_id,
                video_path=pub.video_path,
                video_url=pub.video_url,
                description=pub.description,
                scheduled_date=pub.scheduled_date,
                published_date=pub.published_date,
                status=pub.status,
                error_message=pub.error_message,
                created_at=pub.created_at,
                updated_at=pub.updated_at
            )
            for pub in publications
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar publicações: {str(e)}"
        )


@router.delete("/{publication_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_publication(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancela uma publicação"""
    try:
        publication_repo = PublicationQueueRepository(db)
        scheduler_service = PublicationSchedulerService(publication_repo)
        publication_service = PublicationService(publication_repo, scheduler_service)
        
        success = publication_service.cancel_publication(publication_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Publicação não encontrada ou não pode ser cancelada"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao cancelar publicação: {str(e)}"
        )

