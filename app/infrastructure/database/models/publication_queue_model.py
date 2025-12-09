from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base
from app.domain.entities.publication_queue import PublicationStatus


class PublicationQueueModel(Base):
    """Model SQLAlchemy para PublicationQueue"""
    __tablename__ = "publication_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    video_path = Column(String(500), nullable=False)
    video_url = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    scheduled_date = Column(DateTime(timezone=True), nullable=True, index=True)
    published_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(SQLEnum(PublicationStatus), default=PublicationStatus.PENDING, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("UserModel", back_populates="publication_queue")
    
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

