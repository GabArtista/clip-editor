from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.Providers.DatabaseServiceProvider import Base
from app.domain.entities.video_edit import VideoEditStatus


class VideoEdit(Base):
    """Model SQLAlchemy para VideoEdit"""
    __tablename__ = "video_edits"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    music_id = Column(Integer, ForeignKey("musics.id", ondelete="SET NULL"), nullable=False)
    local_file_path = Column(String(500), nullable=False)
    s3_key = Column(String(500), nullable=False)
    s3_url = Column(String(500), nullable=False)
    preview_url = Column(String(500), nullable=False)
    status = Column(SQLEnum(VideoEditStatus), default=VideoEditStatus.PENDING_APPROVAL, nullable=False, index=True)
    description = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True, index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    delete_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    music = relationship("Music", foreign_keys=[music_id])
    
    def to_domain(self) -> "VideoEdit":
        """Converte model para entidade de domínio"""
        from app.domain.entities.video_edit import VideoEdit
        return VideoEdit(
            id=self.id,
            user_id=self.user_id,
            music_id=self.music_id,
            local_file_path=self.local_file_path,
            s3_key=self.s3_key,
            s3_url=self.s3_url,
            preview_url=self.preview_url,
            status=self.status,
            description=self.description or "",
            expires_at=self.expires_at,
            published_at=self.published_at,
            delete_at=self.delete_at,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

