from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.publication_queue import PublicationQueue


class IPublicationQueueRepository(ABC):
    """Contrato do repositório de fila de publicações."""

    @abstractmethod
    def create(self, publication: PublicationQueue) -> PublicationQueue:
        ...

    @abstractmethod
    def get_by_id(self, publication_id: int) -> Optional[PublicationQueue]:
        ...

    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PublicationQueue]:
        ...

    @abstractmethod
    def get_upcoming_from_now(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PublicationQueue]:
        ...

    @abstractmethod
    def get_pending_for_month(self, user_id: int, year: int, month: int) -> List[PublicationQueue]:
        ...

    @abstractmethod
    def get_scheduled_for_today(self) -> List[PublicationQueue]:
        ...

    @abstractmethod
    def count_by_user_and_month(self, user_id: int, year: int, month: int) -> int:
        ...

    @abstractmethod
    def update(self, publication: PublicationQueue) -> PublicationQueue:
        ...

    @abstractmethod
    def delete(self, publication_id: int) -> bool:
        ...


