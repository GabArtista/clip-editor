from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.entities.video_edit import VideoEdit, VideoEditStatus


class IVideoEditRepository(ABC):
    """Interface do repositório de vídeos editados"""
    
    @abstractmethod
    def create(self, video_edit: VideoEdit) -> VideoEdit:
        """Cria um novo vídeo editado"""
        pass
    
    @abstractmethod
    def get_by_id(self, video_edit_id: int) -> Optional[VideoEdit]:
        """Busca vídeo editado por ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[VideoEdit]:
        """Lista vídeos editados de um usuário"""
        pass
    
    @abstractmethod
    def get_pending_approval(self, user_id: int) -> List[VideoEdit]:
        """Lista vídeos pendentes de aprovação do usuário"""
        pass
    
    @abstractmethod
    def get_expired_previews(self, current_time: datetime) -> List[VideoEdit]:
        """Lista vídeos com preview expirado"""
        pass
    
    @abstractmethod
    def get_to_delete(self, current_time: datetime) -> List[VideoEdit]:
        """Lista vídeos que devem ser deletados"""
        pass
    
    @abstractmethod
    def update(self, video_edit: VideoEdit) -> VideoEdit:
        """Atualiza um vídeo editado"""
        pass
    
    @abstractmethod
    def delete(self, video_edit_id: int) -> bool:
        """Deleta um vídeo editado"""
        pass

