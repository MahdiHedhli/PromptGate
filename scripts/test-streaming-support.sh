#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

port="${PROMPTGATE_STREAMING_TEST_PORT:-8796}"
token="${PROMPTGATE_AUTH_TOKEN:-}"
gateway_pid=""

if [[ -z "$token" ]]; then
  echo "FAIL: PROMPTGATE_AUTH_TOKEN is not configured. Run ./scripts/setup-local-key.sh first." >&2
  exit 1
fi

response_file="$(mktemp)"
cleanup() {
  rm -f "$response_file"
  if [[ -n "$gateway_pid" ]]; then
    kill "$gateway_pid" >/dev/null 2>&1 || true
    wait "$gateway_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT

if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "FAIL: streaming support test port ${port} is already in use" >&2
  lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2
  exit 1
fi

py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
PROMPTGATE_PROVIDER_MODE=mock "$py" -m uvicorn promptgate.server:app --host 127.0.0.1 --port "$port" >/tmp/promptgate-streaming-support.log 2>&1 &
gateway_pid="$!"
for _ in {1..40}; do
  curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1 && break
  sleep 0.25
done
if ! curl -fsS "http://127.0.0.1:${port}/health" >/dev/null 2>&1; then
  echo "FAIL: PromptGate did not start for streaming support test" >&2
  sed -E 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' /tmp/promptgate-streaming-support.log >&2 || true
  exit 1
fi

curl -fsS -X POST "http://127.0.0.1:${port}/mock/reset" >/dev/null

status="$(curl -sS -o "$response_file" -w "%{http_code}" "http://127.0.0.1:${port}/v1/chat/completions" \
  -H "Authorization: Bearer ${token}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","stream":true,"messages":[{"role":"user","content":"Email alice@example.com from 10.1.2.3"}]}')"

if [[ "$status" != "200" ]]; then
  echo "FAIL: expected streaming request to succeed with HTTP 200 after scan/rewrite, got ${status}" >&2
  sed -E 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' "$response_file" >&2
  exit 1
fi

if ! grep -F -q "data: [DONE]" "$response_file"; then
  echo "FAIL: streaming response did not include the expected SSE terminator" >&2
  sed -E 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' "$response_file" >&2
  exit 1
fi

if curl -fsS "http://127.0.0.1:${port}/mock/received" | grep -F -q -e "alice@example.com" -e "10.1.2.3"; then
  echo "FAIL: raw sensitive value reached mock provider during streaming" >&2
  exit 1
fi

echo "PASS: streaming request was authenticated, scanned, rewritten, and streamed safely"
