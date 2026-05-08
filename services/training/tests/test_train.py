"""Unit tests for services/training/train.py."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from pipeline import LeafAnalysisPipeline
from services.training import train as train_module


def test_extract_features_returns_2d_float32(synthetic_dataset: Path) -> None:
    """extract_features must stack vectors into a (N, D) float32 matrix."""
    paths = sorted(str(p) for p in synthetic_dataset.rglob("*.png"))
    pipeline = LeafAnalysisPipeline(
        preprocess_filter="gaussian",
        segmentation_method="otsu",
        morphology_operations=["closing"],
        apply_mask_to_features=True,
        descriptor="lbp",
    )
    matrix = train_module.extract_features(paths, pipeline)
    assert matrix.ndim == 2
    assert matrix.dtype == np.float32
    assert matrix.shape[0] == len(paths)


def test_train_main_writes_all_artifacts(
    synthetic_dataset: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """train.main must produce the five contract artifacts on a tiny dataset."""
    out_dir = tmp_path / "artifacts"
    argv = [
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
    ]
    monkeypatch.setattr(sys, "argv", argv)
    train_module.main()

    expected = {
        "model.joblib",
        "pipeline_config.json",
        "label_names.json",
        "metrics.json",
        "metadata.json",
    }
    assert expected.issubset({p.name for p in out_dir.iterdir()})
