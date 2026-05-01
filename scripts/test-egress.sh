#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
port="${PROMPTGATE_EGRESS_PORT:-8795}"
base="http://127.0.0.1:${port}"
token="${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}"
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
tmp_log="$(mktemp)"
server_pid=""

cleanup() {
  if [[ -n "$server_pid" ]]; then
    kill "$server_pid" >/dev/null 2>&1 || true
  fi
  rm -f "$tmp_log"
}
trap cleanup EXIT

"$py" -m uvicorn promptgate.server:app --host 127.0.0.1 --port "$port" >"$tmp_log" 2>&1 &
server_pid="$!"
for _ in {1..40}; do
  curl -fsS "$base/health" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS "$base/health" >/dev/null

curl -fsS -X POST "$base/mock/reset" >/dev/null

echo "1) Benign request should reach provider"
curl -fsS "$base/v1/chat/completions" \
  -H "Authorization: Bearer ${token}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Summarize release notes for public docs."}]}' >/dev/null

echo "2) Tokenized email/IP should reach provider without raw values"
curl -fsS "$base/v1/chat/completions" \
  -H "Authorization: Bearer ${token}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Email alice@example.com from 10.1.2.3 about Project Raven."}]}' >/dev/null

echo "3) Secret should be blocked before provider"
status=$(curl -sS -o /tmp/promptgate-block.json -w "%{http_code}" "$base/v1/chat/completions" \
  -H "Authorization: Bearer ${token}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Use sk-abc1234567890SECRET for the demo."}]}')
test "$status" = "400"

received="$(curl -fsS "$base/mock/received")"
echo "$received"
if echo "$received" | grep -E 'alice@example.com|10\.1\.2\.3|sk-abc1234567890SECRET' >/dev/null; then
  echo "FAIL: raw sensitive value reached mock provider" >&2
  exit 1
fi
echo "PASS: mock provider did not receive raw sensitive values"
