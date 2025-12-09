from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from app.domain.entities.template import TemplateType


class TemplateCreateDTO(BaseModel):
    """DTO para criação de template"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_type: TemplateType = TemplateType.COMPLETE
    config: Dict[str, Any] = Field(default_factory=dict)
    thumbnail_url: Optional[str] = None
    is_public: bool = False


class TemplateUpdateDTO(BaseModel):
    """DTO para atualização de template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    template_type: Optional[TemplateType] = None
    config: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    is_public: Optional[bool] = None


class TemplateResponseDTO(BaseModel):
    """DTO de resposta de template"""
    id: int
    name: str
    description: Optional[str] = None
    template_type: TemplateType
    config: Dict[str, Any]
    thumbnail_url: Optional[str] = None
    is_public: bool
    created_by: Optional[int] = None
    usage_count: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

