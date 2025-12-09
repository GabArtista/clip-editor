from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class VideoEditStatus(str, Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"
    EXPIRED = "expired"


@dataclass
class VideoEdit:
    """Entidade de domínio VideoEdit - vídeos editados aguardando aprovação"""
    id: Optional[int] = None
    user_id: int = 0
    music_id: int = 0
    local_file_path: str = ""  # Caminho local antes do S3
    s3_key: str = ""  # Chave no S3
    s3_url: str = ""  # URL pública do S3
    preview_url: str = ""  # URL pré-assinada temporária (5 min)
    status: VideoEditStatus = VideoEditStatus.PENDING_APPROVAL
    description: str = ""  # Descrição para publicação (preenchida na aprovação)
    expires_at: Optional[datetime] = None  # Expiração do preview (5 min)
    published_at: Optional[datetime] = None  # Quando foi publicado
    delete_at: Optional[datetime] = None  # Quando deve ser deletado (3h após publicação)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_expired(self, current_time: datetime) -> bool:
        """Verifica se o preview expirou"""
        if not self.expires_at:
            return False
        return current_time > self.expires_at
    
    def should_be_deleted(self, current_time: datetime) -> bool:
        """Verifica se deve ser deletado (3h após publicação)"""
        if not self.delete_at:
            return False
        return current_time > self.delete_at

