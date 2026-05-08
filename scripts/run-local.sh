#!/usr/bin/env bash
set -euo pipefail
# Bring the local stack up or down via docker-compose.
# Usage:
#   ./scripts/run-local.sh         -> up (build + detached)
#   ./scripts/run-local.sh down    -> stop and remove containers
#   ./scripts/run-local.sh logs    -> follow logs

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "created .env from .env.example — edit it if you need different credentials"
fi

case "${1:-up}" in
  up)
    docker compose up --build -d
    docker compose ps
    echo
    echo "stack is up:"
    echo "  auth       -> http://localhost:8001/docs"
    echo "  classifier -> http://localhost:8002/docs"
    ;;
  down)
    docker compose down
    ;;
  logs)
    docker compose logs -f --tail=100
    ;;
  *)
    echo "usage: $0 [up|down|logs]" >&2
    exit 1
    ;;
esac
