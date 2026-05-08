"""JWT-only auth dependency for the classifier service.

Intentionally smaller than the auth-service security module: this service
trusts the signed `sub` claim and does not hit the users table. That keeps
the two services independently deployable and removes auth-service from
the request path of every prediction.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from jose import jwt

from .config import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def get_current_user_id(
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> int:
    """Decode the Bearer token and return the user id stored in `sub`."""
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "not authenticated")
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        return int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "invalid token")
