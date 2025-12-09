from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.domain.entities.user import UserRole


class CreateUserRequest(BaseModel):
    """Request para criação de usuário"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    webhook_url: Optional[str] = Field(None, description="URL do webhook para publicações")
    role: UserRole = UserRole.USER
