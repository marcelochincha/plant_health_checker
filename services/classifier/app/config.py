"""Classifier service configuration loaded from environment / .env."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class Settings(BaseSettings):
    """Settings driven by environment variables; the .env file is optional."""

    database_url: str = (
        "postgresql+psycopg2://leaf_app:leaf_app@postgres:5432/leaf_app"
    )
    jwt_secret: str = "change-me-in-prod"
    jwt_algorithm: str = "HS256"
    artifacts_dir: Path = Path("services/classifier/artifacts")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
