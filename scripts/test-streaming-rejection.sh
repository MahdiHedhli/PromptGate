#!/usr/bin/env bash
set -euo pipefail

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

port="${PROMPTGATE_PORT:-8787}"
token="${PROMPTGATE_AUTH_TOKEN:-}"

if [[ -z "$token" ]]; then
  echo "FAIL: PROMPTGATE_AUTH_TOKEN is not configured. Run ./scripts/setup-local-key.sh first." >&2
  exit 1
fi

response_file="$(mktemp)"
cleanup() {
  rm -f "$response_file"
}
trap cleanup EXIT

status="$(curl -sS -o "$response_file" -w "%{http_code}" "http://127.0.0.1:${port}/v1/chat/completions" \
  -H "Authorization: Bearer ${token}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","stream":true,"messages":[{"role":"user","content":"hello"}]}')"

if [[ "$status" != "400" ]]; then
  echo "FAIL: expected streaming request to be rejected with HTTP 400, got ${status}" >&2
  sed -E 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' "$response_file" >&2
  exit 1
fi

if ! grep -F -q "rejects streaming requests safely" "$response_file"; then
  echo "FAIL: streaming rejection response did not include the expected safety message" >&2
  sed -E 's/(Bearer )[A-Za-z0-9._-]+/\1[REDACTED]/g' "$response_file" >&2
  exit 1
fi

echo "PASS: streaming request was scanned path-authenticated and rejected safely"
