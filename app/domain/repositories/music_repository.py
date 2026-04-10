from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.music import Music


class IMusicRepository(ABC):
    """Contrato do repositório de músicas."""

    @abstractmethod
    def create(self, music: Music) -> Music:
        ...

    @abstractmethod
    def get_by_id(self, music_id: int) -> Optional[Music]:
        ...

    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Music]:
        ...

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Music]:
        ...

    @abstractmethod
    def update(self, music: Music) -> Music:
        ...

    @abstractmethod
    def delete(self, music_id: int) -> bool:
        ...

    @abstractmethod
    def get_by_name_and_user(self, name: str, user_id: int) -> Optional[Music]:
        ...


