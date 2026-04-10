from typing import Optional, Any
from pydantic import BaseModel, Field


class TemplateCreateDTO(BaseModel):
    """Payload para criação de template."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    template_type: str = Field(..., min_length=1, max_length=100)
    config: Any
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    is_public: bool = True


class TemplateUpdateDTO(BaseModel):
    """Payload para atualização parcial de template."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    template_type: Optional[str] = Field(None, min_length=1, max_length=100)
    config: Optional[Any] = None
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class TemplateResponseDTO(BaseModel):
    """Resposta padronizada de template."""

    id: int
    name: str
    description: Optional[str]
    template_type: str
    config: Any
    thumbnail_url: Optional[str]
    is_public: bool
    created_by: int
    usage_count: int
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


