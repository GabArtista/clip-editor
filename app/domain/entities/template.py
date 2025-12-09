from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class TemplateType(str, Enum):
    """Tipos de template"""
    TRANSITION = "transition"
    FILTER = "filter"
    EFFECT = "effect"
    OVERLAY = "overlay"
    COMPLETE = "complete"


@dataclass
class Template:
    """Entidade de domínio Template"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    template_type: TemplateType = TemplateType.COMPLETE
    config: Dict[str, Any] = None  # Configurações do template (JSON)
    thumbnail_url: Optional[str] = None
    is_public: bool = False
    created_by: Optional[int] = None  # ID do usuário que criou
    usage_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}

