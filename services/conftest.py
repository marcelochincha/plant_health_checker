"""Shared fixtures for training and classifier tests — synthetic data only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2
import joblib
import numpy as np
import pytest
from sklearn.svm import SVC


_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _make_leaf_image(shape: tuple[int, int] = (64, 64), seed: int = 0) -> np.ndarray:
    """Generate a small BGR image that survives gaussian + otsu + lbp without errors."""
    rng = np.random.default_rng(seed)
    image = rng.integers(0, 255, size=(shape[0], shape[1], 3), dtype=np.uint8)
    cv2.rectangle(image, (10, 10), (shape[1] - 10, shape[0] - 10), (40, 200, 60), -1)
    return image


@pytest.fixture
def synthetic_image_bytes() -> bytes:
    """A PNG-encoded synthetic leaf image."""
    image = _make_leaf_image(seed=1)
    ok, buf = cv2.imencode(".png", image)
    assert ok, "cv2.imencode should succeed on a valid array."
    return buf.tobytes()


@pytest.fixture
def synthetic_dataset(tmp_path: Path) -> Path:
    """Build a PlantVillage-style dataset with two classes and a handful of images."""
    root = tmp_path / "dataset"
    healthy = root / "Tomato___healthy"
    diseased = root / "Tomato___Bacterial_spot"
    healthy.mkdir(parents=True)
    diseased.mkdir(parents=True)

    for idx in range(4):
        cv2.imwrite(str(healthy / f"img_{idx}.png"), _make_leaf_image(seed=idx))
        cv2.imwrite(
            str(diseased / f"img_{idx}.png"),
            _make_leaf_image(seed=100 + idx),
        )
    return root


@pytest.fixture
def tmp_artifacts(tmp_path: Path, synthetic_image_bytes: bytes) -> Path:
    """A minimal artifacts directory backed by a trivially-trained classifier.

    Uses descriptor='lbp' so the feature dimension is fully determined by
    LeafAnalysisPipeline at inference time. The dummy model is trained on
    feature vectors extracted from the same synthetic image so dimensions
    line up regardless of LBP parameters.
    """
    from pipeline import LeafAnalysisPipeline

    config = {
        "preprocess_filter": "gaussian",
        "segmentation_method": "otsu",
        "morphology_operations": ["closing"],
        "apply_mask_to_features": True,
        "descriptor": "lbp",
    }

    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    seed_image_path = tmp_path / "seed.png"
    seed_image_path.write_bytes(synthetic_image_bytes)
    pipe = LeafAnalysisPipeline(**config)
    feature = pipe.transform(str(seed_image_path))
    feature_dim = feature.shape[0]

    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, feature_dim)).astype(np.float32)
    y = rng.integers(0, 2, size=20)
    model = SVC(probability=True).fit(X, y)

    joblib.dump(model, artifacts / "model.joblib")
    (artifacts / "pipeline_config.json").write_text(json.dumps(config))
    (artifacts / "label_names.json").write_text(
        json.dumps(["healthy", "not_healthy"])
    )
    return artifacts
