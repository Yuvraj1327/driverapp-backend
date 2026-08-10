"""
Auth-related schemas: login, tokens.
"""
import uuid

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    """Public self-registration. Always creates a 'driver' role account —
    elevated roles (admin/manager) must be created via /users by an admin."""

    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=6, max_length=100)


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    role: str | None = None
    type: str | None = None
    exp: int | None = None
