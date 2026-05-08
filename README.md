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

## Scripts

Bash automation lives under `scripts/`. Run from the repo root.

| Script | Purpose |
| --- | --- |
| `scripts/clone.sh [dest]` | Clone the repo into `dest` (defaults to `plant_health_checker`) and check out `develop`. Override the URL with `REPO_URL=...`. |
| `scripts/test.sh` | Provision a local `.venv`, install root + per-service requirements, run the full `pytest` suite. Set `SKIP_INTEGRATION=1` to skip endpoint tests that need a live Postgres. |
| `scripts/run-local.sh [up\|down\|logs]` | Bring the docker-compose stack up (default), tear it down, or follow logs. Auto-creates `.env` from `.env.example` on first run. |
| `scripts/train.sh` | Run the training container against `DATASET_PATH`. Optional `SAMPLE_FRACTION` (defaults to `0.3`). |

## Kubernetes (future)

Manifest skeletons live under [`infra/k8s/`](infra/k8s/README.md) — a
namespace, a Postgres Deployment + Service, and a Deployment + Service per
microservice. They are not part of the milestone delivery, but
`kubectl apply --dry-run=client -f infra/k8s/` validates the full set so
the architecture stays portable.

## Continuous Integration

GitHub Actions runs on every push and pull request to `develop` and `main`
(see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)):

1. `unit-tests`: provisions Postgres 16, installs root + per-service
   requirements, runs the full `pytest` suite with `DATABASE_URL_TEST`
   wired to the service container.
2. `docker-build` (depends on `unit-tests`): builds all three images to
   catch Dockerfile regressions before merge.

## Workflow

This project follows GitFlow with Conventional Commits. Feature branches are
created off `develop` and merged back via pull requests.
