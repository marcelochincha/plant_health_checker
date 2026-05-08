"""Unit tests for services/training/evaluate.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from services.training import evaluate as evaluate_module
from services.training import train as train_module


def test_evaluate_writes_report(
    synthetic_dataset: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """evaluate.main must reload artifacts and persist evaluate_report.json."""
    out_dir = tmp_path / "artifacts"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "train.py",
            "--dataset",
            str(synthetic_dataset),
            "--out",
            str(out_dir),
            "--sample-fraction",
            "1.0",
            "--test-size",
            "0.5",
            "--descriptor",
            "lbp",
        ],
    )
    train_module.main()

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "evaluate.py",
            "--artifacts",
            str(out_dir),
            "--dataset",
            str(synthetic_dataset),
            "--sample-fraction",
            "1.0",
        ],
    )
    evaluate_module.main()

    report_path = out_dir / "evaluate_report.json"
    assert report_path.exists()
    report = json.loads(report_path.read_text())
    for key in ("accuracy", "f1_weighted", "confusion_matrix", "classification_report"):
        assert key in report
