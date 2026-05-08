"""Evaluate a serialized leaf-health model against a dataset and persist the report."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
from sklearn.metrics import accuracy_score
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.metrics import f1_score

from dataset import build_dataset
from pipeline import LeafAnalysisPipeline
from services.training.train import extract_features


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments for the evaluate entrypoint."""
    parser = argparse.ArgumentParser(
        description="Evaluate an already-trained leaf health classifier."
    )
    parser.add_argument(
        "--artifacts",
        type=Path,
        required=True,
        help="Directory containing model.joblib, pipeline_config.json, label_names.json.",
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Root PlantVillage-style directory used as the evaluation set.",
    )
    parser.add_argument("--sample-fraction", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    """Load artifacts, score the model on the dataset, and write evaluate_report.json."""
    args = parse_args()

    config = json.loads((args.artifacts / "pipeline_config.json").read_text())
    label_names = json.loads((args.artifacts / "label_names.json").read_text())
    model = joblib.load(args.artifacts / "model.joblib")

    paths, labels, _ = build_dataset(
        args.dataset,
        mode="binary",
        sample_fraction=args.sample_fraction,
        balance=True,
        random_state=args.random_state,
    )

    pipe = LeafAnalysisPipeline(**config)
    pipe.fit(list(paths))
    X = extract_features(list(paths), pipe)
    y = labels[: len(X)]

    preds = model.predict(X)
    report = {
        "accuracy": float(accuracy_score(y, preds)),
        "f1_weighted": float(f1_score(y, preds, average="weighted")),
        "confusion_matrix": confusion_matrix(y, preds).tolist(),
        "classification_report": classification_report(
            y, preds, target_names=label_names, output_dict=True
        ),
    }

    print(json.dumps(report, indent=2))
    (args.artifacts / "evaluate_report.json").write_text(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
