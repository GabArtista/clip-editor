from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.domain.entities.user import UserRole


class UpdateUserRequest(BaseModel):
    """Request para atualização de usuário"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    webhook_url: Optional[str] = Field(None, description="URL do webhook para publicações")
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
