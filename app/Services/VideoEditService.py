from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.domain.entities.video_edit import VideoEdit, VideoEditStatus
from app.domain.repositories.video_edit_repository import IVideoEditRepository
from app.infrastructure.storage import S3Client
from config import settings
import os
import uuid
import logging

logger = logging.getLogger(__name__)
SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class VideoEditService:
    """Serviço de domínio para vídeos editados"""
    
    def __init__(
        self,
        video_edit_repo: IVideoEditRepository,
        s3_client: S3Client
    ):
        self.video_edit_repo = video_edit_repo
        self.s3_client = s3_client
    
    def create_video_edit(
        self,
        user_id: int,
        music_id: int,
        local_file_path: str,
        user_uuid: str = None
    ) -> VideoEdit:
        """
        Cria registro de vídeo editado e faz upload para S3
        
        Args:
            user_id: ID do usuário
            music_id: ID da música usada
            local_file_path: Caminho local do vídeo processado
            user_uuid: UUID do usuário (opcional, será buscado se não fornecido)
        
        Returns:
            VideoEdit criado com URLs
        """
        if not os.path.exists(local_file_path):
            raise ValueError(f"Arquivo não encontrado: {local_file_path}")
        
        # Busca user_uuid se não fornecido
        if not user_uuid:
            from app.Providers.DatabaseServiceProvider import SessionLocal
            from app.Models.User import User as UserModel
            db = SessionLocal()
            try:
                db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
                if not db_user:
                    raise ValueError(f"Usuário {user_id} não encontrado")
                user_uuid = str(db_user.uuid)
            finally:
                db.close()
        
        # Gera chave única no S3 usando user_uuid
        filename = os.path.basename(local_file_path)
        s3_key = f"video-edits/{user_uuid}/{uuid.uuid4().hex}_{filename}"
        
        # Faz upload para S3 (público)
        s3_url = self.s3_client.upload_file(
            file_path=local_file_path,
            s3_key=s3_key,
            content_type="video/mp4",
            public=True
        )
        
        # Gera URL pré-assinada temporária (5 minutos)
        preview_url = self.s3_client.generate_presigned_url(
            s3_key=s3_key,
            expiration=settings.VIDEO_PREVIEW_EXPIRATION_MINUTES * 60
        )
        
        # Calcula expiração do preview
        expires_at = datetime.now(SP_TIMEZONE) + timedelta(
            minutes=settings.VIDEO_PREVIEW_EXPIRATION_MINUTES
        )
        
        # Cria registro
        video_edit = VideoEdit(
            user_id=user_id,
            music_id=music_id,
            local_file_path=local_file_path,
            s3_key=s3_key,
            s3_url=s3_url,
            preview_url=preview_url,
            status=VideoEditStatus.PENDING_APPROVAL,
            expires_at=expires_at
        )
        
        return self.video_edit_repo.create(video_edit)
    
    def create_video_edit_without_upload(
        self,
        user_id: int,
        music_id: int,
        local_file_path: str,
        base_url: str = "http://127.0.0.1:8060",
        user_uuid: str = None
    ) -> VideoEdit:
        """
        Cria registro de vídeo editado SEM fazer upload S3 (upload será feito em background)
        
        Args:
            user_id: ID do usuário
            music_id: ID da música usada
            local_file_path: Caminho local do vídeo processado
            base_url: URL base da API para gerar URL local temporária
            user_uuid: UUID do usuário (opcional, será buscado se não fornecido)
        
        Returns:
            VideoEdit criado com status PROCESSING_UPLOAD
        """
        if not os.path.exists(local_file_path):
            raise ValueError(f"Arquivo não encontrado: {local_file_path}")
        
        # Busca user_uuid se não fornecido
        if not user_uuid:
            from app.Providers.DatabaseServiceProvider import SessionLocal
            from app.Models.User import User as UserModel
            db = SessionLocal()
            try:
                db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
                if not db_user:
                    raise ValueError(f"Usuário {user_id} não encontrado")
                user_uuid = str(db_user.uuid)
            finally:
                db.close()
        
        filename = os.path.basename(local_file_path)
        
        # Gera URL local temporária usando user_uuid (até upload S3 concluir)
        video_url = f"{base_url}/api/v1/videos/files/{user_uuid}/{filename}"
        
        # Calcula expiração do preview (5 minutos)
        expires_at = datetime.now(SP_TIMEZONE) + timedelta(
            minutes=settings.VIDEO_PREVIEW_EXPIRATION_MINUTES
        )
        
        # Cria registro com status PROCESSING_UPLOAD
        video_edit = VideoEdit(
            user_id=user_id,
            music_id=music_id,
            local_file_path=local_file_path,
            s3_key="",  # Será preenchido após upload S3
            s3_url=video_url,  # URL local temporária
            preview_url=video_url,  # URL local temporária
            status=VideoEditStatus.PROCESSING_UPLOAD,
            expires_at=expires_at
        )
        
        return self.video_edit_repo.create(video_edit)
    
    def create_video_edit_local(
        self,
        user_id: int,
        music_id: int,
        local_file_path: str,
        base_url: str = "http://127.0.0.1:8060",
        user_uuid: str = None
    ) -> VideoEdit:
        """
        Cria registro de vídeo editado usando armazenamento local (fallback quando S3 falha)
        
        Args:
            user_id: ID do usuário
            music_id: ID da música usada
            local_file_path: Caminho local do vídeo processado
            base_url: URL base da API para gerar URL local
            user_uuid: UUID do usuário (opcional, será buscado se não fornecido)
        
        Returns:
            VideoEdit criado com URLs locais
        """
        if not os.path.exists(local_file_path):
            raise ValueError(f"Arquivo não encontrado: {local_file_path}")
        
        # Busca user_uuid se não fornecido
        if not user_uuid:
            from app.Providers.DatabaseServiceProvider import SessionLocal
            from app.Models.User import User as UserModel
            db = SessionLocal()
            try:
                db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
                if not db_user:
                    raise ValueError(f"Usuário {user_id} não encontrado")
                user_uuid = str(db_user.uuid)
            finally:
                db.close()
        
        filename = os.path.basename(local_file_path)
        
        # Gera URL local usando user_uuid
        video_url = f"{base_url}/api/v1/videos/files/{user_uuid}/{filename}"
        
        # Calcula expiração do preview (5 minutos)
        expires_at = datetime.now(SP_TIMEZONE) + timedelta(
            minutes=settings.VIDEO_PREVIEW_EXPIRATION_MINUTES
        )
        
        # Cria registro com armazenamento local
        video_edit = VideoEdit(
            user_id=user_id,
            music_id=music_id,
            local_file_path=local_file_path,
            s3_key="",  # Vazio quando não está no S3
            s3_url=video_url,  # Usa URL local como s3_url para compatibilidade
            preview_url=video_url,  # URL local também serve como preview
            status=VideoEditStatus.PENDING_APPROVAL,
            expires_at=expires_at
        )
        
        return self.video_edit_repo.create(video_edit)
    
    def approve_video(
        self,
        video_edit_id: int,
        user_id: int,
        description: str
    ) -> VideoEdit:
        """
        Aprova vídeo editado e agenda na fila de publicação
        
        Args:
            video_edit_id: ID do vídeo editado
            user_id: ID do usuário (validação)
            description: Descrição para publicação
        
        Returns:
            VideoEdit atualizado
        """
        video_edit = self.video_edit_repo.get_by_id(video_edit_id)
        if not video_edit:
            raise ValueError("Vídeo editado não encontrado")
        
        if video_edit.user_id != user_id:
            raise ValueError("Vídeo não pertence ao usuário")
        
        if video_edit.status != VideoEditStatus.PENDING_APPROVAL:
            raise ValueError("Vídeo já foi processado")
        
        # Verifica se expires_at está definido (segurança extra)
        if not video_edit.expires_at:
            raise ValueError("Vídeo sem data de expiração definida")
        
        # Verifica se não expirou (usa timezone consistente)
        current_time = datetime.now(SP_TIMEZONE)
        if video_edit.is_expired(current_time):
            video_edit.status = VideoEditStatus.EXPIRED
            self.video_edit_repo.update(video_edit)
            raise ValueError("Preview do vídeo expirou. Processe novamente.")
        
        # Atualiza status e descrição
        video_edit.status = VideoEditStatus.APPROVED
        video_edit.description = description
        
        return self.video_edit_repo.update(video_edit)
    
    def reject_video(self, video_edit_id: int, user_id: int) -> bool:
        """
        Rejeita vídeo editado (deleta do S3 e banco)
        
        Args:
            video_edit_id: ID do vídeo editado
            user_id: ID do usuário (validação)
        
        Returns:
            True se deletado
        """
        video_edit = self.video_edit_repo.get_by_id(video_edit_id)
        if not video_edit:
            return False
        
        if video_edit.user_id != user_id:
            raise ValueError("Vídeo não pertence ao usuário")
        
        # Deleta do S3
        self.s3_client.delete_file(video_edit.s3_key)
        
        # Deleta do banco
        return self.video_edit_repo.delete(video_edit_id)
    
    def mark_as_published(self, video_edit_id: int) -> VideoEdit:
        """
        Marca vídeo como publicado e agenda deleção (3h depois)
        
        Args:
            video_edit_id: ID do vídeo editado
        
        Returns:
            VideoEdit atualizado
        """
        video_edit = self.video_edit_repo.get_by_id(video_edit_id)
        if not video_edit:
            raise ValueError("Vídeo editado não encontrado")
        
        video_edit.status = VideoEditStatus.PUBLISHED
        video_edit.published_at = datetime.now(SP_TIMEZONE)
        video_edit.delete_at = datetime.now(SP_TIMEZONE) + timedelta(
            hours=settings.VIDEO_DELETE_AFTER_PUBLICATION_HOURS
        )
        
        return self.video_edit_repo.update(video_edit)
    
    def cleanup_expired(self) -> int:
        """
        Limpa vídeos com preview expirado (não aprovados)
        Inclui vídeos PENDING_APPROVAL expirados e vídeos marcados como EXPIRED
        
        Returns:
            Número de vídeos deletados
        """
        current_time = datetime.now(SP_TIMEZONE)
        
        # Busca vídeos PENDING_APPROVAL expirados
        expired_pending = self.video_edit_repo.get_expired_previews(current_time)
        
        # Busca vídeos EXPIRED (marcados manualmente na aprovação)
        expired_marked = self.video_edit_repo.get_by_status(VideoEditStatus.EXPIRED)
        
        # Filtra apenas os que realmente expiraram (segurança extra)
        expired_marked = [v for v in expired_marked if v.is_expired(current_time)]
        
        # Combina todas as listas
        all_expired = expired_pending + expired_marked
        
        deleted = 0
        for video in all_expired:
            try:
                # Deleta do S3 (se tiver s3_key)
                if video.s3_key:
                    self.s3_client.delete_file(video.s3_key)
                # Deleta do banco
                self.video_edit_repo.delete(video.id)
                deleted += 1
            except Exception as e:
                logger.error(f"Erro ao limpar vídeo {video.id}: {e}", exc_info=True)
        
        return deleted
    
    def cleanup_published(self) -> int:
        """
        Limpa vídeos publicados após 3 horas
        
        Returns:
            Número de vídeos deletados
        """
        current_time = datetime.now(SP_TIMEZONE)
        to_delete = self.video_edit_repo.get_to_delete(current_time)
        
        deleted = 0
        for video in to_delete:
            try:
                # Deleta do S3
                self.s3_client.delete_file(video.s3_key)
                # Deleta do banco
                self.video_edit_repo.delete(video.id)
                deleted += 1
            except Exception as e:
                logger.error(f"Erro ao deletar vídeo publicado {video.id}: {e}", exc_info=True)
        
        return deleted

