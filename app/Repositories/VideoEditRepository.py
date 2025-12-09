from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.domain.entities.video_edit import VideoEdit, VideoEditStatus
from app.domain.repositories.video_edit_repository import IVideoEditRepository
from app.Models.video_edit_model import VideoEdit


class VideoEditRepository(IVideoEditRepository):
    """Implementação do repositório de vídeos editados"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, video_edit: VideoEdit) -> VideoEdit:
        """Cria um novo vídeo editado"""
        db_video = VideoEdit(
            user_id=video_edit.user_id,
            music_id=video_edit.music_id,
            local_file_path=video_edit.local_file_path,
            s3_key=video_edit.s3_key,
            s3_url=video_edit.s3_url,
            preview_url=video_edit.preview_url,
            status=video_edit.status,
            description=video_edit.description,
            expires_at=video_edit.expires_at,
            published_at=video_edit.published_at,
            delete_at=video_edit.delete_at
        )
        self.db.add(db_video)
        self.db.commit()
        self.db.refresh(db_video)
        return db_video.to_domain()
    
    def get_by_id(self, video_edit_id: int) -> Optional[VideoEdit]:
        """Busca vídeo editado por ID"""
        db_video = self.db.query(VideoEdit).filter(
            VideoEdit.id == video_edit_id
        ).first()
        return db_video.to_domain() if db_video else None
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[VideoEdit]:
        """Lista vídeos editados de um usuário"""
        db_videos = self.db.query(VideoEdit).filter(
            VideoEdit.user_id == user_id
        ).offset(skip).limit(limit).order_by(VideoEdit.created_at.desc()).all()
        return [v.to_domain() for v in db_videos]
    
    def get_pending_approval(self, user_id: int) -> List[VideoEdit]:
        """Lista vídeos pendentes de aprovação do usuário"""
        db_videos = self.db.query(VideoEdit).filter(
            and_(
                VideoEdit.user_id == user_id,
                VideoEdit.status == VideoEditStatus.PENDING_APPROVAL
            )
        ).order_by(VideoEdit.created_at.desc()).all()
        return [v.to_domain() for v in db_videos]
    
    def get_expired_previews(self, current_time: datetime) -> List[VideoEdit]:
        """Lista vídeos com preview expirado"""
        db_videos = self.db.query(VideoEdit).filter(
            and_(
                VideoEdit.status == VideoEditStatus.PENDING_APPROVAL,
                VideoEdit.expires_at < current_time
            )
        ).all()
        return [v.to_domain() for v in db_videos]
    
    def get_to_delete(self, current_time: datetime) -> List[VideoEdit]:
        """Lista vídeos que devem ser deletados"""
        db_videos = self.db.query(VideoEdit).filter(
            and_(
                VideoEdit.delete_at.isnot(None),
                VideoEdit.delete_at < current_time
            )
        ).all()
        return [v.to_domain() for v in db_videos]
    
    def update(self, video_edit: VideoEdit) -> VideoEdit:
        """Atualiza um vídeo editado"""
        db_video = self.db.query(VideoEdit).filter(
            VideoEdit.id == video_edit.id
        ).first()
        if not db_video:
            raise ValueError(f"Vídeo editado com ID {video_edit.id} não encontrado")
        
        db_video.s3_key = video_edit.s3_key
        db_video.s3_url = video_edit.s3_url
        db_video.preview_url = video_edit.preview_url
        db_video.status = video_edit.status
        db_video.description = video_edit.description
        db_video.expires_at = video_edit.expires_at
        db_video.published_at = video_edit.published_at
        db_video.delete_at = video_edit.delete_at
        
        self.db.commit()
        self.db.refresh(db_video)
        return db_video.to_domain()
    
    def delete(self, video_edit_id: int) -> bool:
        """Deleta um vídeo editado"""
        db_video = self.db.query(VideoEdit).filter(
            VideoEdit.id == video_edit_id
        ).first()
        if not db_video:
            return False
        
        self.db.delete(db_video)
        self.db.commit()
        return True

