"""Pydantic request/response models for the auth endpoints."""
from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field


class RegisterIn(BaseModel):
    """Body for POST /auth/register."""

    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)


class LoginIn(BaseModel):
    """Body for POST /auth/login."""

    email: EmailStr
    password: str


class UserOut(BaseModel):
    """Public representation of a user — never includes the password hash."""

    id: int
    username: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TokenOut(BaseModel):
    """Response shape for a successful login."""

    access_token: str
    token_type: str = "bearer"
