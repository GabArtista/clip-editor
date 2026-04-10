"""
Job assíncrono para upload de vídeos para S3 em background
Permite resposta rápida ao usuário enquanto upload acontece em background
"""
import logging
from sqlalchemy.orm import Session
from app.Providers.DatabaseServiceProvider import SessionLocal
from app.Repositories.VideoEditRepository import VideoEditRepository
from app.Services.VideoEditService import VideoEditService
from app.infrastructure.storage.s3_client import S3Client
from app.domain.entities.video_edit import VideoEditStatus

logger = logging.getLogger(__name__)


class VideoUploadWorker:
    """Worker para upload assíncrono de vídeos para S3"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.video_edit_repo = VideoEditRepository(self.db)
        self.s3_client = S3Client()
        self.video_edit_service = VideoEditService(self.video_edit_repo, self.s3_client)
    
    def upload_video_to_s3(self, video_edit_id: int) -> bool:
        """
        Faz upload de vídeo para S3 em background
        
        Args:
            video_edit_id: ID do vídeo editado
            
        Returns:
            True se upload bem-sucedido
        """
        try:
            video_edit = self.video_edit_repo.get_by_id(video_edit_id)
            if not video_edit:
                logger.error(f"Vídeo editado {video_edit_id} não encontrado")
                return False
            
            # Se já tem S3 key e URL não é local, não precisa fazer upload novamente
            if video_edit.s3_key and video_edit.s3_url and not video_edit.s3_url.startswith("http://127.0.0.1") and not video_edit.s3_url.startswith("http://localhost"):
                logger.info(f"Vídeo {video_edit_id} já está no S3: {video_edit.s3_url}")
                return True
            
            # Se não tem arquivo local, não pode fazer upload
            import os
            if not os.path.exists(video_edit.local_file_path):
                logger.error(f"Arquivo local não encontrado: {video_edit.local_file_path}")
                # Atualiza status para indicar erro
                video_edit.status = VideoEditStatus.PENDING_APPROVAL
                video_edit.s3_url = f"http://127.0.0.1:8060/api/v1/videos/files/{video_edit.user_id}/{os.path.basename(video_edit.local_file_path)}"
                self.video_edit_repo.update(video_edit)
                return False
            
            # Busca user_uuid para usar no S3 key
            from app.Models.User import User as UserModel
            db_user = self.db.query(UserModel).filter(UserModel.id == video_edit.user_id).first()
            if not db_user:
                logger.error(f"Usuário {video_edit.user_id} não encontrado")
                return False
            user_uuid = str(db_user.uuid)
            
            # Gera chave única no S3 usando user_uuid
            import uuid
            filename = os.path.basename(video_edit.local_file_path)
            s3_key = f"video-edits/{user_uuid}/{uuid.uuid4().hex}_{filename}"
            
            # Faz upload para S3
            logger.info(f"Iniciando upload S3 para vídeo {video_edit_id}: {s3_key}")
            s3_url = self.s3_client.upload_file(
                file_path=video_edit.local_file_path,
                s3_key=s3_key,
                content_type="video/mp4",
                public=True
            )
            
            # Gera URL pré-assinada temporária (5 minutos)
            from config import settings
            from datetime import datetime, timedelta
            from zoneinfo import ZoneInfo
            
            try:
                preview_url = self.s3_client.generate_presigned_url(
                    s3_key=s3_key,
                    expiration=settings.VIDEO_PREVIEW_EXPIRATION_MINUTES * 60
                )
            except Exception as e:
                logger.warning(f"Erro ao gerar URL pré-assinada, usando URL pública: {e}")
                preview_url = s3_url
            
            # Atualiza expires_at
            SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")
            expires_at = datetime.now(SP_TIMEZONE) + timedelta(
                minutes=settings.VIDEO_PREVIEW_EXPIRATION_MINUTES
            )
            
            # Atualiza registro com URLs S3
            video_edit.s3_key = s3_key
            video_edit.s3_url = s3_url
            video_edit.preview_url = preview_url
            video_edit.status = VideoEditStatus.PENDING_APPROVAL
            video_edit.expires_at = expires_at
            
            self.video_edit_repo.update(video_edit)
            
            logger.info(f"Upload S3 concluído para vídeo {video_edit_id}: {s3_url}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao fazer upload S3 para vídeo {video_edit_id}: {e}", exc_info=True)
            
            # Atualiza status para PENDING_APPROVAL com URL local usando UUID (fallback)
            try:
                video_edit = self.video_edit_repo.get_by_id(video_edit_id)
                if video_edit:
                    import os
                    from app.Models.User import User as UserModel
                    filename = os.path.basename(video_edit.local_file_path)
                    
                    # Busca user_uuid
                    db_user = self.db.query(UserModel).filter(UserModel.id == video_edit.user_id).first()
                    user_uuid = str(db_user.uuid) if db_user else str(video_edit.user_id)
                    
                    from config import settings
                    base_url = f"http://{settings.APP_HOST}:{settings.APP_PORT}"
                    video_edit.status = VideoEditStatus.PENDING_APPROVAL
                    video_edit.s3_url = f"{base_url}/api/v1/videos/files/{user_uuid}/{filename}"
                    video_edit.preview_url = video_edit.s3_url
                    self.video_edit_repo.update(video_edit)
                    logger.info(f"Vídeo {video_edit_id} atualizado com URL local usando UUID (fallback)")
            except Exception as e2:
                logger.error(f"Erro ao atualizar vídeo com fallback: {e2}")
            
            return False
        finally:
            self.db.close()


def process_video_upload(video_edit_id: int):
    """Função para ser chamada pelo scheduler ou worker assíncrono"""
    worker = VideoUploadWorker()
    return worker.upload_video_to_s3(video_edit_id)

