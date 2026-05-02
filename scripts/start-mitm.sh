#!/usr/bin/env bash
set -euo pipefail
mkdir -p local/runtime/mitm
proxy_port="${PROMPTGATE_MITM_PROXY_PORT:-8898}"
compose_build_flag="--build"
if docker image inspect promptgate_mitm-fake-upstream:latest >/dev/null 2>&1; then
  compose_build_flag="--no-build"
fi
COMPOSE_PROJECT_NAME=promptgate_mitm PROMPTGATE_MITM_PROXY_PORT="$proxy_port" docker compose -f docker-compose.mitm.yml up -d "$compose_build_flag"
echo "MITM fake-upstream stack started."
echo "Proxy: http://127.0.0.1:${proxy_port}"
echo "Captures: local/runtime/mitm/"
