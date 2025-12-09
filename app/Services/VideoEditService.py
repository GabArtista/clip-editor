from typing import Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from app.domain.entities.video_edit import VideoEdit, VideoEditStatus
from app.domain.repositories.video_edit_repository import IVideoEditRepository
from app.infrastructure.storage import S3Client
from config import settings
import os
import uuid

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
        local_file_path: str
    ) -> VideoEdit:
        """
        Cria registro de vídeo editado e faz upload para S3
        
        Args:
            user_id: ID do usuário
            music_id: ID da música usada
            local_file_path: Caminho local do vídeo processado
        
        Returns:
            VideoEdit criado com URLs
        """
        if not os.path.exists(local_file_path):
            raise ValueError(f"Arquivo não encontrado: {local_file_path}")
        
        # Gera chave única no S3
        filename = os.path.basename(local_file_path)
        s3_key = f"video-edits/{user_id}/{uuid.uuid4().hex}_{filename}"
        
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
        
        # Verifica se não expirou
        if video_edit.is_expired(datetime.now(SP_TIMEZONE)):
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
        
        Returns:
            Número de vídeos deletados
        """
        current_time = datetime.now(SP_TIMEZONE)
        expired = self.video_edit_repo.get_expired_previews(current_time)
        
        deleted = 0
        for video in expired:
            try:
                # Deleta do S3
                self.s3_client.delete_file(video.s3_key)
                # Deleta do banco
                self.video_edit_repo.delete(video.id)
                deleted += 1
            except Exception as e:
                print(f"Erro ao limpar vídeo {video.id}: {e}")
        
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
                print(f"Erro ao deletar vídeo publicado {video.id}: {e}")
        
        return deleted

