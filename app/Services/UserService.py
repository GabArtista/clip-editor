from typing import Optional
from app.domain.entities.user import User, UserRole
from app.domain.repositories.user_repository import IUserRepository
from app.Helpers.PasswordHelper import get_password_hash, verify_password


class UserService:
    """Serviço de domínio para usuários"""
    
    def __init__(self, user_repository: IUserRepository):
        self.user_repository = user_repository
    
    def create_user(
        self,
        email: str,
        username: str,
        password: str,
        role: UserRole = UserRole.USER,
        webhook_url: Optional[str] = None
    ) -> User:
        """Cria um novo usuário"""
        # Verifica se email já existe
        if self.user_repository.get_by_email(email):
            raise ValueError("Email já está em uso")
        
        # Verifica se username já existe
        if self.user_repository.get_by_username(username):
            raise ValueError("Username já está em uso")
        
        # Cria usuário
        user = User(
            email=email,
            username=username,
            password_hash=get_password_hash(password),
            webhook_url=webhook_url,
            role=role,
            is_active=True,
            is_blocked=False
        )
        
        return self.user_repository.create(user)
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Autentica um usuário"""
        user = self.user_repository.get_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.password_hash):
            return None
        
        if not user.can_access():
            return None
        
        return user
    
    def update_user(self, user_id: int, **kwargs) -> User:
        """Atualiza um usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Atualiza campos permitidos
        if "email" in kwargs and kwargs["email"] != user.email:
            if self.user_repository.get_by_email(kwargs["email"]):
                raise ValueError("Email já está em uso")
            user.email = kwargs["email"]
        
        if "username" in kwargs and kwargs["username"] != user.username:
            if self.user_repository.get_by_username(kwargs["username"]):
                raise ValueError("Username já está em uso")
            user.username = kwargs["username"]
        
        if "password" in kwargs:
            user.password_hash = get_password_hash(kwargs["password"])
        
        if "role" in kwargs:
            user.role = kwargs["role"]
        
        if "is_active" in kwargs:
            user.is_active = kwargs["is_active"]
        
        if "is_blocked" in kwargs:
            user.is_blocked = kwargs["is_blocked"]
        
        if "webhook_url" in kwargs:
            user.webhook_url = kwargs["webhook_url"]
        
        return self.user_repository.update(user)
    
    def block_user(self, user_id: int) -> User:
        """Bloqueia um usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        user.is_blocked = True
        return self.user_repository.update(user)
    
    def unblock_user(self, user_id: int) -> User:
        """Desbloqueia um usuário"""
        user = self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        user.is_blocked = False
        return self.user_repository.update(user)

