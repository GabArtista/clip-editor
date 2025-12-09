from typing import Optional, List
from sqlalchemy.orm import Session
from app.domain.entities.user import User
from app.domain.repositories.user_repository import IUserRepository
from app.infrastructure.database.models.user_model import UserModel


class UserRepository(IUserRepository):
    """Implementação do repositório de usuários"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user: User) -> User:
        """Cria um novo usuário"""
        db_user = UserModel(
            email=user.email,
            username=user.username,
            password_hash=user.password_hash,
            role=user.role,
            is_active=user.is_active,
            is_blocked=user.is_blocked
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user.to_domain()
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário por ID"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return db_user.to_domain() if db_user else None
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário por email"""
        db_user = self.db.query(UserModel).filter(UserModel.email == email).first()
        return db_user.to_domain() if db_user else None
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Busca usuário por username"""
        db_user = self.db.query(UserModel).filter(UserModel.username == username).first()
        return db_user.to_domain() if db_user else None
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Lista todos os usuários"""
        db_users = self.db.query(UserModel).offset(skip).limit(limit).all()
        return [user.to_domain() for user in db_users]
    
    def update(self, user: User) -> User:
        """Atualiza um usuário"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not db_user:
            raise ValueError(f"Usuário com ID {user.id} não encontrado")
        
        db_user.email = user.email
        db_user.username = user.username
        if user.password_hash:
            db_user.password_hash = user.password_hash
        db_user.role = user.role
        db_user.is_active = user.is_active
        db_user.is_blocked = user.is_blocked
        
        self.db.commit()
        self.db.refresh(db_user)
        return db_user.to_domain()
    
    def delete(self, user_id: int) -> bool:
        """Deleta um usuário"""
        db_user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not db_user:
            return False
        
        self.db.delete(db_user)
        self.db.commit()
        return True

