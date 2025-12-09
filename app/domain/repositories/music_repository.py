from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.music import Music


class IMusicRepository(ABC):
    """Interface do repositório de músicas"""
    
    @abstractmethod
    def create(self, music: Music) -> Music:
        """Cria uma nova música"""
        pass
    
    @abstractmethod
    def get_by_id(self, music_id: int) -> Optional[Music]:
        """Busca música por ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Music]:
        """Lista músicas de um usuário"""
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Music]:
        """Lista todas as músicas"""
        pass
    
    @abstractmethod
    def update(self, music: Music) -> Music:
        """Atualiza uma música"""
        pass
    
    @abstractmethod
    def delete(self, music_id: int) -> bool:
        """Deleta uma música"""
        pass
    
    @abstractmethod
    def get_by_name_and_user(self, name: str, user_id: int) -> Optional[Music]:
        """Busca música por nome e usuário"""
        pass

