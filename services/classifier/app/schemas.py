"""Pydantic models for the classifier HTTP layer."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class PredictionOut(BaseModel):
    """Public representation of a stored prediction row."""

    id: int
    user_id: int
    label: str
    confidence: float
    image_filename: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
