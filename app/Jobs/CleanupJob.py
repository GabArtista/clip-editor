"""
Worker para limpeza de vídeos expirados do S3
Executa periodicamente para limpar:
- Vídeos com preview expirado (não aprovados em 5 min)
- Vídeos publicados há mais de 3 horas
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.orm import Session
from app.Providers.DatabaseServiceProvider import SessionLocal
from app.Repositories.VideoEditRepository import VideoEditRepository
from app.Services.VideoEditService import VideoEditService
from app.infrastructure.storage.s3_client import S3Client

logger = logging.getLogger(__name__)
SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class CleanupWorker:
    """Worker para limpeza de vídeos do S3"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.video_edit_repo = VideoEditRepository(self.db)
        self.s3_client = S3Client()
        self.video_edit_service = VideoEditService(self.video_edit_repo, self.s3_client)
    
    def cleanup_expired_previews(self) -> int:
        """
        Limpa vídeos com preview expirado (não aprovados em 5 min)
        
        Returns:
            Número de vídeos deletados
        """
        try:
            logger.info("Iniciando limpeza de previews expirados...")
            deleted = self.video_edit_service.cleanup_expired()
            logger.info(f"Limpeza concluída: {deleted} vídeos deletados")
            return deleted
        except Exception as e:
            logger.error(f"Erro na limpeza de previews: {str(e)}", exc_info=True)
            return 0
        finally:
            self.db.close()
    
    def cleanup_published_videos(self) -> int:
        """
        Limpa vídeos publicados há mais de 3 horas
        
        Returns:
            Número de vídeos deletados
        """
        try:
            logger.info("Iniciando limpeza de vídeos publicados...")
            deleted = self.video_edit_service.cleanup_published()
            logger.info(f"Limpeza concluída: {deleted} vídeos deletados")
            return deleted
        except Exception as e:
            logger.error(f"Erro na limpeza de vídeos publicados: {str(e)}", exc_info=True)
            return 0
        finally:
            self.db.close()
    
    def run_cleanup(self):
        """Executa todas as limpezas"""
        expired = self.cleanup_expired_previews()
        published = self.cleanup_published_videos()
        return expired + published


def run_cleanup_worker():
    """Função para ser chamada pelo scheduler"""
    worker = CleanupWorker()
    worker.run_cleanup()

