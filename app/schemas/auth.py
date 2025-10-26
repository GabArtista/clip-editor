from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AuthRegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=72)

    @field_validator("email")
    @classmethod
    def _validate_email(cls, value: str) -> str:
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("E-mail inválido.")
        local, domain = value.split("@", 1)
        if not local or not domain or "." not in domain:
            raise ValueError("E-mail inválido.")
        return value

    @field_validator("password")
    @classmethod
    def _validate_password(cls, value: str) -> str:
        if len(value.strip()) == 0:
            raise ValueError("Senha não pode ser vazia.")
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Senha deve possuir no máximo 72 bytes.")
        return value


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserSummary"


class UserSummary(BaseModel):
    id: str
    email: str


class AuthMeResponse(UserSummary):
    pass


TokenResponse.model_rebuild()
