"""HTTP routes that implement the auth contract: register, login, me."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import User
from ..schemas import LoginIn
from ..schemas import RegisterIn
from ..schemas import TokenOut
from ..schemas import UserOut
from ..security import create_access_token
from ..security import get_current_user
from ..security import hash_password
from ..security import verify_password


router = APIRouter()


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
)
def register(
    body: RegisterIn,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Create a new user; reject duplicate email/username with 400."""
    existing = db.scalar(
        select(User).where(
            (User.email == body.email) | (User.username == body.username)
        )
    )
    if existing is not None:
        if existing.email == body.email:
            raise HTTPException(400, "email already registered")
        raise HTTPException(400, "username already taken")

    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "user already exists")
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenOut)
def login(
    body: LoginIn,
    db: Annotated[Session, Depends(get_db)],
) -> TokenOut:
    """Verify credentials and mint a JWT signed with the configured secret."""
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    return TokenOut(access_token=create_access_token(user))


@router.get("/me", response_model=UserOut)
def me(user: Annotated[User, Depends(get_current_user)]) -> User:
    """Return the user identified by the Bearer token."""
    return user
