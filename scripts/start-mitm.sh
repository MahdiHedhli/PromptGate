#!/usr/bin/env bash
set -euo pipefail
mkdir -p local/runtime/mitm
proxy_port="${PROMPTGATE_MITM_PROXY_PORT:-8898}"
COMPOSE_PROJECT_NAME=promptgate_mitm PROMPTGATE_MITM_PROXY_PORT="$proxy_port" docker compose -f docker-compose.mitm.yml up -d --build
echo "MITM fake-upstream stack started."
echo "Proxy: http://127.0.0.1:${proxy_port}"
echo "Captures: local/runtime/mitm/"
