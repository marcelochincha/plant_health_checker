"""End-to-end test: register on auth-service, login, predict, list history.

Exercises the cross-service contract that both apps validate the SAME JWT
locally with the SAME secret. The auth-service mints; the classifier-service
trusts the signature and reads `sub`.
"""
from __future__ import annotations

import io
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture
def auth_client(db_session: Session) -> Iterator[TestClient]:
    """TestClient for the auth service backed by the shared test database."""
    from services.auth.app.db import get_db as auth_get_db
    from services.auth.app.main import app as auth_app

    def _override() -> Iterator[Session]:
        yield db_session

    auth_app.dependency_overrides[auth_get_db] = _override
    with TestClient(auth_app) as client:
        yield client
    auth_app.dependency_overrides.clear()


@pytest.fixture
def classifier_client(
    db_session: Session, stub_classifier_predict: MagicMock
) -> Iterator[TestClient]:
    """TestClient for the classifier service sharing the same DB session."""
    from services.classifier.app import inference_singleton
    from services.classifier.app.db import get_db as cls_get_db
    from services.classifier.app.main import app as cls_app

    inference_singleton._clf = stub_classifier_predict

    def _override() -> Iterator[Session]:
        yield db_session

    cls_app.dependency_overrides[cls_get_db] = _override
    with TestClient(cls_app) as client:
        yield client
    cls_app.dependency_overrides.clear()
    inference_singleton._clf = None


def _png_bytes() -> bytes:
    return (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\rIDATx\x9cc\xfa\xcf\x00\x00\x00\x02\x00\x01"
        b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )


def test_register_login_predict_history_round_trip(
    auth_client: TestClient,
    classifier_client: TestClient,
    db_session: Session,
) -> None:
    """Full flow: auth mints a token, classifier accepts it, history reflects it."""
    register = auth_client.post(
        "/auth/register",
        json={
            "username": "endtoend",
            "email": "e2e@example.com",
            "password": "secret123",
        },
    )
    assert register.status_code == 201

    login = auth_client.post(
        "/auth/login",
        json={"email": "e2e@example.com", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    predict = classifier_client.post(
        "/classifier/predict",
        headers=headers,
        files={"file": ("e2e.png", io.BytesIO(_png_bytes()), "image/png")},
    )
    assert predict.status_code == 200, predict.text
    body = predict.json()
    assert body["label"] == "healthy"
    assert isinstance(body["user_id"], int)

    history = classifier_client.get("/classifier/predictions", headers=headers)
    assert history.status_code == 200
    rows = history.json()
    assert len(rows) == 1
    assert rows[0]["image_filename"] == "e2e.png"
