# Plant Health Checker

Leaf Health Classifier — backend that classifies images of leaves as `healthy` or
`unhealthy` and persists the prediction history per authenticated user.

## Architecture

3 microservices + Postgres orchestrated with `docker-compose`:

- `auth-service` (FastAPI :8001) — registration, login, JWT issuance.
- `classifier-service` (FastAPI :8002) — prediction endpoint and history.
- `training` (job, profile-gated) — trains the model and produces artifacts
  consumed by `classifier-service`.

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

## Prerequisites

- Docker 24+ and `docker compose` v2
- Python 3.11+ (only required to run the test suite outside Docker)
- (Optional) PlantVillage dataset under `./datasets/PlantVillage`

## How to run

```bash
cp .env.example .env
docker compose up --build         # postgres + auth + classifier
# in another terminal, train the model:
docker compose run --rm training python train.py --dataset /datasets/PlantVillage
```

## How to run the tests

See [`.todo/TESTING.md`](.todo/TESTING.md) for a fresh-machine walkthrough.
TL;DR:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install pytest
pytest -v
```

## Repository layout

- `pipeline.py`, `features.py`, `processing.py`, `dataset.py`, `classifiers.py` —
  shared computer-vision libraries used by both training and inference.
- `tests/` — unit tests for the shared libraries.
- `services/auth/` — FastAPI auth service (users, JWT).
- `services/classifier/` — FastAPI classifier service (predict, history).
- `services/training/` — offline training job that produces model artifacts.
- `infra/k8s/` — Kubernetes manifest skeletons (future deployment target).
- `scripts/` — bash automation (clone, test, run-local, train).
- `.github/workflows/` — CI pipeline.

## Stack

Python 3.11, FastAPI, SQLAlchemy 2.x, Postgres 16, OpenCV, scikit-image,
scikit-learn, Docker, docker-compose.

## Workflow

This project follows GitFlow with Conventional Commits. Feature branches are
created off `develop` and merged back via pull requests.
