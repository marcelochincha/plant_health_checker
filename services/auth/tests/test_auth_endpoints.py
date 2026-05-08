"""Functional tests for /auth/register, /auth/login, /auth/me."""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from services.auth.app.db import get_db
from services.auth.app.main import app


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """TestClient backed by the per-test SQLAlchemy session."""

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _register(client: TestClient, **overrides: str):
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret123",
    }
    payload.update(overrides)
    return client.post("/auth/register", json=payload)


def test_register_returns_201(client: TestClient) -> None:
    """POST /auth/register on a fresh DB returns 201 with the created user."""
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert body["email"] == "alice@example.com"
    assert "password" not in body
    assert "password_hash" not in body


def test_register_duplicate_email_returns_400(client: TestClient) -> None:
    """A second register with the same email is rejected with the contract detail."""
    assert _register(client).status_code == 201
    second = _register(client, username="alice2")
    assert second.status_code == 400
    assert second.json()["detail"] == "email already registered"


def test_register_duplicate_username_returns_400(client: TestClient) -> None:
    """A second register with the same username (different email) is also 400."""
    assert _register(client).status_code == 201
    second = _register(client, email="other@example.com")
    assert second.status_code == 400
    assert second.json()["detail"] == "username already taken"


def test_login_then_me_round_trip(client: TestClient) -> None:
    """register -> login -> GET /me returns the same user."""
    assert _register(client).status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert isinstance(token, str) and token.count(".") == 2

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "alice@example.com"


def test_login_wrong_password_returns_401(client: TestClient) -> None:
    """A bad password produces the contract 'invalid credentials' detail."""
    assert _register(client).status_code == 201
    login = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "WRONG"},
    )
    assert login.status_code == 401
    assert login.json()["detail"] == "invalid credentials"


def test_me_without_token_returns_401(client: TestClient) -> None:
    """GET /auth/me without a Bearer header is rejected."""
    response = client.get("/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "not authenticated"


def test_me_with_invalid_token_returns_401(client: TestClient) -> None:
    """A garbage Bearer token produces the contract 'invalid token' detail."""
    response = client.get(
        "/auth/me", headers={"Authorization": "Bearer not.a.real.token"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "invalid token"
