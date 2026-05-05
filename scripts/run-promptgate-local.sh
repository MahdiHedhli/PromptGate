#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "FAIL: .env is missing. Run ./scripts/setup-local-key.sh first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

port="${PROMPTGATE_PORT:-8787}"

if [[ -z "${PROMPTGATE_AUTH_TOKEN:-}" && "${PROMPTGATE_UNSAFE_DEV_NO_AUTH:-false}" != "true" ]]; then
  echo "FAIL: PROMPTGATE_AUTH_TOKEN is not configured. Run ./scripts/setup-local-key.sh first." >&2
  exit 1
fi

if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "FAIL: 127.0.0.1:${port} is already in use." >&2
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2
  exit 1
fi

py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi

echo "PromptGate local gateway starting on http://127.0.0.1:${port}"
echo "OpenAI-compatible base URL: http://127.0.0.1:${port}/v1"
echo "Leave this terminal open while testing desktop apps. Press Ctrl-C to stop."
echo "No secrets were printed."

exec "$py" -m uvicorn promptgate.server:app --host 127.0.0.1 --port "$port"
