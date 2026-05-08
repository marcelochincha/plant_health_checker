"""Train the leaf health classifier and serialize the artifacts consumed by inference."""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline as SklearnPipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from dataset import build_dataset
from pipeline import LeafAnalysisPipeline


DEFAULT_PIPELINE_CONFIG: dict[str, Any] = {
    "preprocess_filter": "gaussian",
    "segmentation_method": "otsu",
    "morphology_operations": ["closing", "opening"],
    "apply_mask_to_features": True,
    "descriptor": "hsv_lbp+hog",
}


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the training entrypoint."""
    parser = argparse.ArgumentParser(description="Train leaf health classifier.")
    parser.add_argument(
        "--dataset",
        required=True,
        type=Path,
        help="Root PlantVillage-style directory.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("services/classifier/artifacts"),
        help="Where to write artifacts.",
    )
    parser.add_argument("--sample-fraction", type=float, default=0.3)
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument(
        "--descriptor",
        type=str,
        default=DEFAULT_PIPELINE_CONFIG["descriptor"],
    )
    return parser.parse_args()


def extract_features(paths: list[str], pipeline: LeafAnalysisPipeline) -> np.ndarray:
    """Run pipeline.transform on every path and stack the vectors row-wise.

    Input: list of image paths and an already-fit pipeline.
    Output: (N, D) float32 matrix with one row per successfully decoded image.
    Logic: failures (unreadable images, segmentation errors) are skipped silently
    so a single corrupt file does not abort training.
    """
    vectors: list[np.ndarray] = []
    for path in paths:
        try:
            vectors.append(pipeline.transform(path))
        except (FileNotFoundError, ValueError):
            continue
    if not vectors:
        raise RuntimeError("No features extracted.")
    return np.vstack(vectors).astype(np.float32)


def main() -> None:
    """Run the end-to-end training routine and persist artifacts."""
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    paths, labels, label_names = build_dataset(
        args.dataset,
        mode="binary",
        sample_fraction=args.sample_fraction,
        balance=True,
        random_state=args.random_state,
    )

    train_paths, test_paths, y_train, y_test = train_test_split(
        paths,
        labels,
        test_size=args.test_size,
        stratify=labels,
        random_state=args.random_state,
    )

    config = dict(DEFAULT_PIPELINE_CONFIG)
    config["descriptor"] = args.descriptor

    pipe = LeafAnalysisPipeline(**config)
    pipe.fit(list(train_paths))

    X_train = extract_features(list(train_paths), pipe)
    X_test = extract_features(list(test_paths), pipe)

    model = SklearnPipeline(
        [
            ("scaler", StandardScaler()),
            (
                "clf",
                SVC(
                    kernel="rbf",
                    C=1.0,
                    gamma="scale",
                    probability=True,
                    random_state=args.random_state,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train[: len(X_train)])

    preds = model.predict(X_test)
    y_test_aligned = y_test[: len(preds)]
    metrics = {
        "accuracy": float(accuracy_score(y_test_aligned, preds)),
        "f1_weighted": float(f1_score(y_test_aligned, preds, average="weighted")),
        "confusion_matrix": confusion_matrix(y_test_aligned, preds).tolist(),
    }

    joblib.dump(model, args.out / "model.joblib")
    (args.out / "pipeline_config.json").write_text(json.dumps(config, indent=2))
    (args.out / "label_names.json").write_text(json.dumps(label_names, indent=2))
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2))
    (args.out / "metadata.json").write_text(
        json.dumps(
            {
                "trained_at": datetime.now(timezone.utc).isoformat(),
                "n_train": int(len(X_train)),
                "n_test": int(len(X_test)),
                "model_name": "SVM-rbf",
                "params": {
                    "kernel": "rbf",
                    "C": 1.0,
                    "gamma": "scale",
                    "probability": True,
                },
            },
            indent=2,
        )
    )

    print(f"Wrote artifacts to {args.out.resolve()}")
    print(f"Metrics: {metrics}")


if __name__ == "__main__":
    main()
