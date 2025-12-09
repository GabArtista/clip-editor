from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.domain.entities.user import UserRole


class UserResource(BaseModel):
    """Resource de resposta de usuário"""
    id: int
    email: str
    username: str
    webhook_url: Optional[str] = None
    role: UserRole
    is_active: bool
    is_blocked: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponseResource(BaseModel):
    """Resource de resposta de token"""
    access_token: str
    token_type: str = "bearer"
    user: UserResource
