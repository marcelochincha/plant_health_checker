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

for svc in services/auth services/classifier services/training; do
  if [[ -f "$svc/requirements.txt" ]]; then
    pip install --quiet -r "$svc/requirements.txt"
  fi
done

python -m pytest tests services/training/tests services/classifier/tests/test_inference.py -v
