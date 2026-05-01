#!/usr/bin/env bash
set -euo pipefail
COMPOSE_PROJECT_NAME=promptgate_mitm docker compose -f docker-compose.mitm.yml down
echo "MITM fake-upstream stack stopped."
