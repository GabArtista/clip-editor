from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime
from app.domain.entities.video_edit import VideoEdit, VideoEditStatus


class IVideoEditRepository(ABC):
    """Contrato do repositório de vídeos editados."""

    @abstractmethod
    def create(self, video_edit: VideoEdit) -> VideoEdit:
        ...

    @abstractmethod
    def get_by_id(self, video_edit_id: int) -> Optional[VideoEdit]:
        ...

    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[VideoEdit]:
        ...

    @abstractmethod
    def get_pending_approval(self, user_id: int) -> List[VideoEdit]:
        ...

    @abstractmethod
    def get_by_status(self, status: VideoEditStatus) -> List[VideoEdit]:
        ...

    @abstractmethod
    def get_expired_previews(self, current_time: datetime) -> List[VideoEdit]:
        ...

    @abstractmethod
    def get_to_delete(self, current_time: datetime) -> List[VideoEdit]:
        ...

    @abstractmethod
    def update(self, video_edit: VideoEdit) -> VideoEdit:
        ...

    @abstractmethod
    def delete(self, video_edit_id: int) -> bool:
        ...

