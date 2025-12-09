from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    """Entidade de domínio User"""
    id: Optional[int] = None
    email: str = ""
    username: str = ""
    password_hash: str = ""
    webhook_url: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True
    is_blocked: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_admin(self) -> bool:
        """Verifica se o usuário é admin"""
        return self.role == UserRole.ADMIN
    
    def can_access(self) -> bool:
        """Verifica se o usuário pode acessar o sistema"""
        return self.is_active and not self.is_blocked

