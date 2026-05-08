# Plant Health Checker

Leaf Health Classifier — backend that classifies images of leaves as `healthy` or
`unhealthy` and persists the prediction history per authenticated user.

## Architecture

```
┌──────────────┐        ┌──────────────────┐        ┌──────────────┐
│   Client     │ ─────▶ │  auth-service    │ ─────▶ │  Postgres    │
│ (curl/HTTP)  │        │  (FastAPI :8001) │        │  :5432       │
└──────────────┘        └──────────────────┘        └──────┬───────┘
        │                                                  │
        │ JWT Bearer                                       │
        ▼                                                  │
┌──────────────────────┐                                   │
│ classifier-service   │ ──────────────────────────────────┘
│ (FastAPI :8002)      │
│  + inference (sklearn│
│    model + pipeline) │
└──────────┬───────────┘
           │ reads
           ▼
   services/classifier/artifacts/
       ├── model.joblib
       ├── pipeline_config.json
       └── label_names.json
```

## Repository layout

- `pipeline.py`, `features.py`, `processing.py`, `dataset.py`, `classifiers.py` — shared
  computer-vision libraries used by both training and inference.
- `tests/` — unit tests for the shared libraries.
- `services/training/` — offline pipeline that produces model artifacts.
- `services/classifier/` — online inference service that consumes those artifacts.

## Stack

Python 3.11, FastAPI, SQLAlchemy 2.x, Postgres 16, OpenCV, scikit-image,
scikit-learn, Docker, docker-compose.

## Scripts

Bash automation lives under `scripts/`. Run from the repo root.

| Script | Purpose |
| --- | --- |
| `scripts/clone.sh [dest]` | Clone the repo into `dest` (defaults to `plant_health_checker`) and check out `develop`. Override the URL with `REPO_URL=...`. |
| `scripts/test.sh` | Provision a local `.venv`, install root + per-service requirements, run the full `pytest` suite. Set `SKIP_INTEGRATION=1` to skip endpoint tests that need a live Postgres. |
| `scripts/run-local.sh [up\|down\|logs]` | Bring the docker-compose stack up (default), tear it down, or follow logs. Auto-creates `.env` from `.env.example` on first run. |
| `scripts/train.sh` | Run the training container against `DATASET_PATH`. Optional `SAMPLE_FRACTION` (defaults to `0.3`). |

## Workflow

This project follows GitFlow with Conventional Commits. Feature branches are
created off `develop` and merged back via pull requests.
