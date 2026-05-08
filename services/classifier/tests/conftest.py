"""Shared fixtures for classifier-service HTTP tests."""
from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker


_DEFAULT_TEST_URL = (
    "postgresql+psycopg2://leaf_app:leaf_app@localhost:5432/leaf_app_test"
)


_TEST_URL = os.environ.get("DATABASE_URL_TEST", _DEFAULT_TEST_URL)
os.environ["DATABASE_URL"] = _TEST_URL

_repo_root = Path(__file__).resolve().parents[3]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))


@pytest.fixture(scope="session")
def database_url() -> str:
    """Resolve the test database URL from env, falling back to local Postgres."""
    return _TEST_URL


@pytest.fixture(scope="session")
def _engine(database_url: str):
    """A session-scoped engine for the chosen test database, or skip on failure."""
    eng = create_engine(database_url, future=True)
    try:
        with eng.connect():
            pass
    except OperationalError as exc:
        pytest.skip(f"test database not reachable at {database_url}: {exc}")
    return eng


@pytest.fixture
def db_session(_engine) -> Iterator[Session]:
    """Per-test session that creates and drops the predictions table."""
    from services.classifier.app.db import Base

    Base.metadata.create_all(_engine)
    Session_ = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    session = Session_()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(_engine)


@pytest.fixture
def stub_classifier_predict() -> MagicMock:
    """A predictable stub for LeafClassifier.predict — no real model needed."""
    mock = MagicMock()
    mock.predict.return_value = {
        "label": "healthy",
        "confidence": 0.9,
        "label_index": 0,
    }
    return mock


@pytest.fixture
def client(db_session: Session, stub_classifier_predict: MagicMock):
    """TestClient with the DB and the inference singleton swapped for stubs."""
    from fastapi.testclient import TestClient

    from services.classifier.app import inference_singleton
    from services.classifier.app.db import get_db
    from services.classifier.app.main import app

    inference_singleton._clf = stub_classifier_predict

    def _override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    inference_singleton._clf = None


def make_token(user_id: int, secret: str | None = None) -> str:
    """Forge a JWT exactly the way the auth-service would for tests."""
    from datetime import datetime
    from datetime import timedelta
    from datetime import timezone

    from jose import jwt

    from services.classifier.app.config import settings

    payload = {
        "sub": str(user_id),
        "email": f"user{user_id}@example.com",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
    }
    return jwt.encode(
        payload,
        secret or settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
