#!/usr/bin/env bash
set -euo pipefail
# Run the full pytest suite (root shared libs + every service).
# Requires Python 3.11+. Endpoint tests need a Postgres reachable at
# DATABASE_URL_TEST; if you do not have one, run:
#   SKIP_INTEGRATION=1 ./scripts/test.sh

cd "$(dirname "$0")/.."

if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: python not found on PATH." >&2
  exit 1
fi

python -m venv .venv 2>/dev/null || true
# shellcheck disable=SC1091
source .venv/bin/activate

pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
pip install --quiet pytest

for svc in services/auth services/classifier services/training; do
  if [[ -f "$svc/requirements.txt" ]]; then
    pip install --quiet -r "$svc/requirements.txt"
  fi
done

if [[ "${SKIP_INTEGRATION:-0}" == "1" ]]; then
  pytest tests services/training/tests services/classifier/tests/test_inference.py -v
else
  pytest -v
fi
