"""Inference: load the serialized model + pipeline and predict from raw image bytes."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import cv2
import joblib
import numpy as np

from pipeline import LeafAnalysisPipeline


class LeafClassifier:
    """Load artifacts produced by services/training/train.py and predict."""

    def __init__(self, artifacts_dir: str | Path) -> None:
        """Materialize the model and pipeline from disk.

        Input: directory containing model.joblib, pipeline_config.json,
        label_names.json. Output: ready-to-use classifier instance.
        Logic: fail fast on missing directories so the service crashes at
        startup rather than on the first prediction.
        """
        self._dir = Path(artifacts_dir)
        if not self._dir.exists():
            raise FileNotFoundError(f"artifacts_dir not found: {self._dir}")

        self._model = joblib.load(self._dir / "model.joblib")
        self._config: dict[str, Any] = json.loads(
            (self._dir / "pipeline_config.json").read_text()
        )
        self._labels: list[str] = json.loads(
            (self._dir / "label_names.json").read_text()
        )
        self._pipeline = LeafAnalysisPipeline(**self._config)

    def predict(self, image_bytes: bytes) -> dict:
        """Return label, confidence and label_index for the given image bytes.

        Input: raw bytes of a JPEG/PNG/BMP image. Output: dict with the
        contracted keys label (str), confidence (float in [0, 1]) and
        label_index (int). Logic: decode with OpenCV, persist to a temp
        file because LeafAnalysisPipeline.transform expects a path,
        extract features, run the sklearn pipeline and read back
        predict_proba when available.

        Raises:
            ValueError: when image_bytes cannot be decoded as an image.
        """
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image bytes.")

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            cv2.imwrite(tmp_path, img)
            features = self._pipeline.transform(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        features = features.reshape(1, -1)
        pred_idx = int(self._model.predict(features)[0])

        if hasattr(self._model, "predict_proba"):
            proba = self._model.predict_proba(features)[0]
            confidence = float(proba[pred_idx])
        else:
            confidence = 1.0

        return {
            "label": self._labels[pred_idx],
            "confidence": confidence,
            "label_index": pred_idx,
        }
