# Training service

Offline pipeline that turns a PlantVillage-style dataset into the artifacts the
`classifier` service consumes at runtime. The training service is run on demand
and never on the request path.

## Lifecycle

```
PlantVillage dataset ──► train.py ──► services/classifier/artifacts/ ──► classifier-service
                                          │
                                          └── evaluate.py (re-score without retraining)
```

## Usage

### 1. Train

```bash
python services/training/train.py --dataset $DATASET_PATH
```

The script samples a fraction of every class, builds the
`LeafAnalysisPipeline`, fits an SVC on top of the descriptor vectors and
writes the artifact bundle into `services/classifier/artifacts/`.

Useful flags:

| Flag | Default | Purpose |
| --- | --- | --- |
| `--dataset` | required | Root of a PlantVillage-style directory tree. |
| `--out` | `services/classifier/artifacts` | Where artifacts are written. |
| `--sample-fraction` | `0.3` | Fraction of each class kept for training. |
| `--test-size` | `0.2` | Fraction of the sampled set held out for the test split. |
| `--random-state` | `42` | Seed for sampling and the train/test split. |
| `--descriptor` | `hsv_lbp+hog` | Feature extractor configuration; must match what inference loads. |

### 2. Evaluate

```bash
python services/training/evaluate.py \
    --artifacts services/classifier/artifacts \
    --dataset $DATASET_PATH
```

`evaluate.py` does not retrain. It reloads `model.joblib` together with
`pipeline_config.json` and `label_names.json`, scores the dataset and writes
`evaluate_report.json` next to the model.

## Environment variables

| Variable | Default | Notes |
| --- | --- | --- |
| `DATASET_PATH` | _unset_ | Path to the PlantVillage root. The CLI reads this through `--dataset`. |
| `ARTIFACTS_DIR` | `services/classifier/artifacts` (host) / `/app/artifacts` (container) | Output directory for `train.py` and input directory for `evaluate.py` and the classifier service. |

## Artifacts produced

| File | Role |
| --- | --- |
| `model.joblib` | Fitted scikit-learn `Pipeline` (`StandardScaler` + `SVC`). |
| `pipeline_config.json` | Kwargs used to rebuild `LeafAnalysisPipeline` at inference time. |
| `label_names.json` | Ordered class names: `["healthy", "not_healthy"]`. |
| `metrics.json` | Accuracy, weighted F1 and confusion matrix from training. |
| `metadata.json` | Train timestamp, sample sizes, model name and SVC params. |
| `evaluate_report.json` | Optional report written by `evaluate.py`. |

Artifacts are intentionally excluded from version control via `.gitignore` —
every consumer is expected to regenerate them locally with `train.py`.
