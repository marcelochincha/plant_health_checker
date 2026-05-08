#!/usr/bin/env bash
set -euo pipefail
# Clone the project into a target directory and check out the integration branch.
# Usage: ./scripts/clone.sh [destination]

REPO_URL="${REPO_URL:-https://github.com/marcelochincha/plant_health_checker.git}"
DEST="${1:-plant_health_checker}"

if [[ -d "$DEST" ]]; then
  echo "ERROR: directory '$DEST' already exists." >&2
  exit 1
fi

git clone "$REPO_URL" "$DEST"
cd "$DEST"
git checkout develop || git checkout main
echo "cloned into $(pwd)"
echo "next: cp .env.example .env && ./scripts/test.sh"
