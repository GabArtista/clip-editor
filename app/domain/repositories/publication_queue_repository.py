from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.entities.publication_queue import PublicationQueue, PublicationStatus


class IPublicationQueueRepository(ABC):
    """Interface do repositório de fila de publicações"""
    
    @abstractmethod
    def create(self, publication: PublicationQueue) -> PublicationQueue:
        """Cria uma nova publicação na fila"""
        pass
    
    @abstractmethod
    def get_by_id(self, publication_id: int) -> Optional[PublicationQueue]:
        """Busca publicação por ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PublicationQueue]:
        """Lista publicações de um usuário"""
        pass
    
    @abstractmethod
    def get_pending_for_month(self, user_id: int, year: int, month: int) -> List[PublicationQueue]:
        """Lista publicações pendentes de um mês específico"""
        pass
    
    @abstractmethod
    def get_scheduled_for_today(self) -> List[PublicationQueue]:
        """Lista publicações agendadas para hoje"""
        pass
    
    @abstractmethod
    def count_by_user_and_month(self, user_id: int, year: int, month: int) -> int:
        """Conta publicações agendadas de um usuário em um mês"""
        pass
    
    @abstractmethod
    def update(self, publication: PublicationQueue) -> PublicationQueue:
        """Atualiza uma publicação"""
        pass
    
    @abstractmethod
    def delete(self, publication_id: int) -> bool:
        """Deleta uma publicação"""
        pass

