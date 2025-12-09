from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.Providers.DatabaseServiceProvider import get_db
from app.Repositories.VideoEditRepository import VideoEditRepository, PublicationQueueRepository, UserRepository
from app.domain.entities.user import User
from app.Http.Middleware.AuthMiddleware import get_current_user
from app.Services.VideoEditService import VideoEditService
from app.Services.PublicationService import PublicationService
from app.Services.PublicationSchedulerService import PublicationSchedulerService
from app.infrastructure.storage import S3Client
from app.Http.Requests.Video.ApproveVideoRequest import ApproveVideoRequest as ApproveVideoEditDTO, VideoEditResponseDTO

router = APIRouter(prefix="/api/v1/video-edits", tags=["Video Edits"])


@router.get("", response_model=List[VideoEditResponseDTO])
def list_video_edits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista vídeos editados do usuário"""
    try:
        video_edit_repo = VideoEditRepository(db)
        video_edits = video_edit_repo.get_by_user_id(current_user.id, skip=skip, limit=limit)
        
        return [
            VideoEditResponseDTO(
                id=ve.id,
                user_id=ve.user_id,
                music_id=ve.music_id,
                s3_url=ve.s3_url,
                preview_url=ve.preview_url,
                status=ve.status,
                description=ve.description,
                expires_at=ve.expires_at.isoformat() if ve.expires_at else None,
                published_at=ve.published_at.isoformat() if ve.published_at else None,
                created_at=ve.created_at.isoformat() if ve.created_at else None
            )
            for ve in video_edits
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar vídeos editados: {str(e)}"
        )


@router.get("/pending", response_model=List[VideoEditResponseDTO])
def list_pending_approval(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista vídeos pendentes de aprovação"""
    try:
        video_edit_repo = VideoEditRepository(db)
        video_edits = video_edit_repo.get_pending_approval(current_user.id)
        
        return [
            VideoEditResponseDTO(
                id=ve.id,
                user_id=ve.user_id,
                music_id=ve.music_id,
                s3_url=ve.s3_url,
                preview_url=ve.preview_url,
                status=ve.status,
                description=ve.description,
                expires_at=ve.expires_at.isoformat() if ve.expires_at else None,
                published_at=ve.published_at.isoformat() if ve.published_at else None,
                created_at=ve.created_at.isoformat() if ve.created_at else None
            )
            for ve in video_edits
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar vídeos pendentes: {str(e)}"
        )


@router.get("/{video_edit_id}", response_model=VideoEditResponseDTO)
def get_video_edit(
    video_edit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém um vídeo editado por ID"""
    try:
        video_edit_repo = VideoEditRepository(db)
        video_edit = video_edit_repo.get_by_id(video_edit_id)
        
        if not video_edit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vídeo editado não encontrado"
            )
        
        if video_edit.user_id != current_user.id and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este vídeo"
            )
        
        return VideoEditResponseDTO(
            id=video_edit.id,
            user_id=video_edit.user_id,
            music_id=video_edit.music_id,
            s3_url=video_edit.s3_url,
            preview_url=video_edit.preview_url,
            status=video_edit.status,
            description=video_edit.description,
            expires_at=video_edit.expires_at.isoformat() if video_edit.expires_at else None,
            published_at=video_edit.published_at.isoformat() if video_edit.published_at else None,
            created_at=video_edit.created_at.isoformat() if video_edit.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar vídeo editado: {str(e)}"
        )


@router.post("/approve", status_code=status.HTTP_200_OK)
def approve_video_edit(
    approve_data: ApproveVideoEditDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Aprova vídeo editado e agenda na fila de publicação
    
    Fluxo:
    1. Valida vídeo editado
    2. Aprova e atualiza descrição
    3. Agenda na fila de publicação usando link S3
    """
    try:
        # Verifica se usuário tem webhook configurado
        if not current_user.webhook_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook não configurado. Configure seu webhook URL no perfil."
            )
        
        s3_client = S3Client()
        video_edit_repo = VideoEditRepository(db)
        video_edit_service = VideoEditService(video_edit_repo, s3_client)
        
        # Aprova vídeo
        video_edit = video_edit_service.approve_video(
            video_edit_id=approve_data.video_edit_id,
            user_id=current_user.id,
            description=approve_data.description
        )
        
        # Agenda na fila de publicação usando link S3
        publication_repo = PublicationQueueRepository(db)
        scheduler_service = PublicationSchedulerService(publication_repo)
        publication_service = PublicationService(publication_repo, scheduler_service)
        
        publication = publication_service.queue_publication(
            user_id=current_user.id,
            video_path=video_edit.s3_url,  # S3 URL (path = url para S3)
            video_url=video_edit.s3_url,   # URL pública do S3 para publicação
            description=video_edit.description
        )
        
        # Marca como publicado (agendado)
        video_edit = video_edit_service.mark_as_published(video_edit.id)
        
        return {
            "ok": True,
            "message": "Vídeo aprovado e agendado para publicação",
            "video_edit_id": video_edit.id,
            "publication_id": publication.id,
            "scheduled_date": publication.scheduled_date.isoformat() if publication.scheduled_date else None,
            "s3_url": video_edit.s3_url
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao aprovar vídeo: {str(e)}"
        )


@router.post("/{video_edit_id}/reject", status_code=status.HTTP_200_OK)
def reject_video_edit(
    video_edit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rejeita vídeo editado (deleta do S3 e banco)"""
    try:
        s3_client = S3Client()
        video_edit_repo = VideoEditRepository(db)
        video_edit_service = VideoEditService(video_edit_repo, s3_client)
        
        success = video_edit_service.reject_video(video_edit_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vídeo editado não encontrado"
            )
        
        return {
            "ok": True,
            "message": "Vídeo rejeitado e removido"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao rejeitar vídeo: {str(e)}"
        )

