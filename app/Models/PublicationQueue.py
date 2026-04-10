from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.Providers.DatabaseServiceProvider import Base
from app.domain.entities.publication_queue import PublicationStatus
import uuid


class PublicationStatusType(TypeDecorator):
    """TypeDecorator para garantir que o enum use o valor string"""
    impl = String
    cache_ok = True
    
    def __init__(self):
        super().__init__(length=20)
        self.enum = PublicationStatus
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, PublicationStatus):
            return value.value
        return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return PublicationStatus(value)


class PublicationQueue(Base):
    """Model SQLAlchemy para PublicationQueue"""
    __tablename__ = "publication_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_path = Column(String(500), nullable=False)
    video_url = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(PublicationStatusType(), default=PublicationStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="publication_queue")
    
    def to_domain(self) -> "PublicationQueue":
        """Converte model para entidade de domínio"""
        from app.domain.entities.publication_queue import PublicationQueue
        return PublicationQueue(
            id=self.id,
            user_id=self.user_id,
            video_path=self.video_path,
            video_url=self.video_url,
            description=self.description,
            scheduled_date=self.scheduled_date,
            published_date=self.published_date,
            status=self.status,
            error_message=self.error_message,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

