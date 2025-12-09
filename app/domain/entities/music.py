from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Music:
    """Entidade de domínio Music"""
    id: Optional[int] = None
    user_id: int = 0
    name: str = ""
    filename: str = ""
    file_path: str = ""
    duration: Optional[float] = None
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def is_owned_by(self, user_id: int) -> bool:
        """Verifica se a música pertence ao usuário"""
        return self.user_id == user_id

