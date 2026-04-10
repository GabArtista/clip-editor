from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.user import User


class IUserRepository(ABC):
    """Contrato do repositório de usuários."""

    @abstractmethod
    def create(self, user: User) -> User:
        ...

    @abstractmethod
    def get_by_id(self, user_id: int) -> Optional[User]:
        ...

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        ...

    @abstractmethod
    def get_by_username(self, username: str) -> Optional[User]:
        ...

    @abstractmethod
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        ...

    @abstractmethod
    def update(self, user: User) -> User:
        ...

    @abstractmethod
    def delete(self, user_id: int) -> bool:
        ...


