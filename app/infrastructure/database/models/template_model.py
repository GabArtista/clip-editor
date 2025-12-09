from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base
from app.domain.entities.template import TemplateType


class TemplateModel(Base):
    """Model SQLAlchemy para Template"""
    __tablename__ = "templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    template_type = Column(SQLEnum(TemplateType), default=TemplateType.COMPLETE, nullable=False)
    config = Column(JSON, nullable=False, default={})
    thumbnail_url = Column(String(500), nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    creator = relationship("UserModel", foreign_keys=[created_by])
    
    def to_domain(self) -> "Template":
        """Converte model para entidade de domínio"""
        from app.domain.entities.template import Template
        return Template(
            id=self.id,
            name=self.name,
            description=self.description,
            template_type=self.template_type,
            config=self.config or {},
            thumbnail_url=self.thumbnail_url,
            is_public=self.is_public,
            created_by=self.created_by,
            usage_count=self.usage_count,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

