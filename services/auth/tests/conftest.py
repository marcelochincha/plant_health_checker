"""Shared fixtures for auth-service tests.

The contract decision (closed) is to test against a real Postgres so types do
not drift between test and production. Set DATABASE_URL_TEST to point at a
disposable Postgres database; tests are skipped automatically when nothing is
reachable, so contributors without a local Postgres are not blocked.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker


_DEFAULT_TEST_URL = (
    "postgresql+psycopg2://leaf_app:leaf_app@localhost:5432/leaf_app_test"
)


@pytest.fixture(scope="session")
def database_url() -> str:
    """Resolve the test database URL from env, falling back to local Postgres."""
    return os.environ.get("DATABASE_URL_TEST", _DEFAULT_TEST_URL)


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
    """Per-test session that creates and drops every auth-service table."""
    from services.auth.app.db import Base

    Base.metadata.create_all(_engine)
    Session_ = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    session = Session_()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(_engine)


@pytest.fixture(autouse=True, scope="session")
def _ensure_repo_root_on_path() -> None:
    """Make `from services.auth.app...` importable regardless of cwd."""
    import sys

    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
