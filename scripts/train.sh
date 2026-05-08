#!/usr/bin/env bash
set -euo pipefail
# Train the leaf classifier inside a one-shot training container.
# Usage:
#   DATASET_PATH=/path/to/PlantVillage ./scripts/train.sh
# Optional:
#   SAMPLE_FRACTION=0.3 ./scripts/train.sh

cd "$(dirname "$0")/.."

if [[ -z "${DATASET_PATH:-}" ]]; then
  echo "ERROR: set DATASET_PATH=/path/to/PlantVillage before running." >&2
  exit 1
fi

SAMPLE_FRACTION="${SAMPLE_FRACTION:-0.3}"

docker compose run --rm training \
  python train.py --dataset /datasets/PlantVillage --sample-fraction "$SAMPLE_FRACTION"

echo "artifacts written to services/classifier/artifacts/"
ls -lh services/classifier/artifacts/ || true
