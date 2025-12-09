from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base


class MusicModel(Base):
    """Model SQLAlchemy para Music"""
    __tablename__ = "musics"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    duration = Column(Float, nullable=True)
    file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    owner = relationship("UserModel", back_populates="musics")
    
    def to_domain(self) -> "Music":
        """Converte model para entidade de domínio"""
        from app.domain.entities.music import Music
        return Music(
            id=self.id,
            user_id=self.user_id,
            name=self.name,
            filename=self.filename,
            file_path=self.file_path,
            duration=self.duration,
            file_size=self.file_size,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

