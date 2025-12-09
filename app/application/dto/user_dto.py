from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.domain.entities.user import UserRole


class UserCreateDTO(BaseModel):
    """DTO para criação de usuário"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    webhook_url: Optional[str] = Field(None, description="URL do webhook para publicações")
    role: UserRole = UserRole.USER


class UserUpdateDTO(BaseModel):
    """DTO para atualização de usuário"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    password: Optional[str] = Field(None, min_length=6)
    webhook_url: Optional[str] = Field(None, description="URL do webhook para publicações")
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None


class UserResponseDTO(BaseModel):
    """DTO de resposta de usuário"""
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


class UserLoginDTO(BaseModel):
    """DTO para login"""
    username: str
    password: str


class TokenResponseDTO(BaseModel):
    """DTO de resposta de token"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponseDTO

