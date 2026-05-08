"""Unit tests for password hashing and JWT helpers."""
from __future__ import annotations

import pytest
from jose import JWTError

from services.auth.app.models import User
from services.auth.app.security import create_access_token
from services.auth.app.security import decode_token
from services.auth.app.security import hash_password
from services.auth.app.security import verify_password


def test_hash_password_round_trip() -> None:
    """A correctly-hashed password verifies; a wrong password does not."""
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True
    assert verify_password("not the same", hashed) is False


def test_create_access_token_contains_sub_and_exp() -> None:
    """create_access_token must encode sub=user.id and an expiry claim."""
    user = User(id=42, username="alice", email="alice@example.com", password_hash="x")
    token = create_access_token(user)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["email"] == "alice@example.com"
    assert "exp" in payload


def test_decode_token_invalid_raises() -> None:
    """Garbage tokens must raise jose.JWTError."""
    with pytest.raises(JWTError):
        decode_token("not.a.jwt")
