"""Unit tests for services/classifier/app/inference.py."""
from __future__ import annotations

from pathlib import Path

import pytest

from services.classifier.app.inference import LeafClassifier


def test_predict_returns_expected_keys(
    tmp_artifacts: Path, synthetic_image_bytes: bytes
) -> None:
    """predict must return exactly label, confidence, label_index for valid bytes."""
    classifier = LeafClassifier(tmp_artifacts)
    result = classifier.predict(synthetic_image_bytes)
    assert set(result.keys()) == {"label", "confidence", "label_index"}
    assert isinstance(result["label"], str)
    assert isinstance(result["label_index"], int)
    assert 0.0 <= result["confidence"] <= 1.0
    assert result["label"] in {"healthy", "not_healthy"}


def test_predict_raises_on_invalid_bytes(tmp_artifacts: Path) -> None:
    """predict must raise ValueError when the bytes cannot be decoded."""
    classifier = LeafClassifier(tmp_artifacts)
    with pytest.raises(ValueError):
        classifier.predict(b"garbage")


def test_init_raises_on_missing_artifacts(tmp_path: Path) -> None:
    """The constructor must fail fast when the artifacts dir is missing."""
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        LeafClassifier(missing)
