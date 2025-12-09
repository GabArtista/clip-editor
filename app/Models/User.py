from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.Providers.DatabaseServiceProvider import Base
from app.domain.entities.user import UserRole


class User(Base):
    """Model SQLAlchemy para User"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    webhook_url = Column(String(500), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_blocked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    musics = relationship("Music", back_populates="owner", cascade="all, delete-orphan")
    publication_queue = relationship("PublicationQueue", back_populates="user", cascade="all, delete-orphan")
    
    def to_domain(self) -> "User":
        """Converte model para entidade de domínio"""
        from app.domain.entities.user import User
        return User(
            id=self.id,
            email=self.email,
            username=self.username,
            password_hash=self.password_hash,
            webhook_url=self.webhook_url,
            role=self.role,
            is_active=self.is_active,
            is_blocked=self.is_blocked,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

