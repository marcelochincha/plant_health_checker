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

## Workflow

This project follows GitFlow with Conventional Commits. Feature branches are
created off `develop` and merged back via pull requests.
