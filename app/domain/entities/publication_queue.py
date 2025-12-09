from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class PublicationStatus(str, Enum):
    PENDING = "pending"
    SCHEDULED = "scheduled"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PublicationQueue:
    """Entidade de domínio PublicationQueue"""
    id: Optional[int] = None
    user_id: int = 0
    video_path: str = ""
    video_url: str = ""
    description: str = ""
    scheduled_date: Optional[datetime] = None
    published_date: Optional[datetime] = None
    status: PublicationStatus = PublicationStatus.PENDING
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def can_be_published(self) -> bool:
        """Verifica se a publicação pode ser processada"""
        return self.status in [PublicationStatus.PENDING, PublicationStatus.SCHEDULED]
    
    def is_past_due(self, current_date: datetime) -> bool:
        """Verifica se a data agendada já passou"""
        if not self.scheduled_date:
            return False
        return self.scheduled_date < current_date

