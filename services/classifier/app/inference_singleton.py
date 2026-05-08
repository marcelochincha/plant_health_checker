"""Module-level cache for the LeafClassifier so it loads once per process."""
from __future__ import annotations

from pathlib import Path

from .inference import LeafClassifier


_clf: LeafClassifier | None = None


def init_classifier(artifacts_dir: Path) -> None:
    """Load model + pipeline from disk once, on application startup."""
    global _clf
    _clf = LeafClassifier(artifacts_dir)


def get_classifier(allow_none: bool = False) -> LeafClassifier | None:
    """Return the cached classifier; raise unless explicitly allowed to be None."""
    if _clf is None and not allow_none:
        raise RuntimeError("classifier not initialized")
    return _clf
