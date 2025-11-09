from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.models import UserStatus


class AuthRegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)
    display_name: Optional[str] = Field(default=None, max_length=255)

    @field_validator("email")
    @classmethod
    def _normalize_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or "." not in value.split("@", 1)[-1]:
            raise ValueError("E-mail inválido.")
        return value


class AuthLoginRequest(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        if len(value.strip()) == 0:
            raise ValueError("Senha não pode ser vazia.")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Senha deve possuir no máximo 72 bytes.")
        return value


class UserSummary(BaseModel):
    id: str
    email: str
    display_name: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserSummary


class AuthMeResponse(UserSummary):
    status: UserStatus
    wallet_balance: Decimal
    currency: str
