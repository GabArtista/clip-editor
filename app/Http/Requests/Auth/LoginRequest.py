from pydantic import BaseModel


class LoginRequest(BaseModel):
    """Request para login"""
    username: str
    password: str
