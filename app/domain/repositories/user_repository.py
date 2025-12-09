from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.entities.user import User


class IUserRepository(ABC):
    """Interface do repositório de usuários"""
    
    @abstractmethod
    def create(self, user: User) -> User:
        """Cria um novo usuário"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email"""
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        """Busca usuário por username"""
        pass
    
    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Lista todos os usuários"""
        pass
    
    @abstractmethod
    def update(self, user: User) -> User:
        """Atualiza um usuário"""
        pass
    
    @abstractmethod
    def delete(self, user_id: int) -> bool:
        """Deleta um usuário"""
        pass

