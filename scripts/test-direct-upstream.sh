#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then set -a; source .env; set +a; fi
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
gateway_port="${PROMPTGATE_TEST_GATEWAY_PORT:-8790}"
upstream_port="${PROMPTGATE_FAKE_UPSTREAM_PORT:-8791}"
capture="docs/reports/generated/fake-upstream-capture.json"
rm -f "$capture"
upstream_pid=""
gateway_pid=""
cleanup() {
  if [[ -n "$gateway_pid" ]]; then
    kill "$gateway_pid" >/dev/null 2>&1 || true
    wait "$gateway_pid" 2>/dev/null || true
  fi
  if [[ -n "$upstream_pid" ]]; then
    kill "$upstream_pid" >/dev/null 2>&1 || true
    wait "$upstream_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT
PROMPTGATE_FAKE_CAPTURE="$capture" "$py" -m uvicorn scripts.fake_upstream:app --host 127.0.0.1 --port "$upstream_port" >/tmp/promptgate-fake-upstream.log 2>&1 &
upstream_pid="$!"
PROMPTGATE_PROVIDER_MODE=upstream \
PROMPTGATE_UPSTREAM_BASE_URL="http://127.0.0.1:${upstream_port}" \
PROMPTGATE_UPSTREAM_API_KEY="fake-upstream-key" \
PROMPTGATE_AUTH_TOKEN="${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}" \
"$py" -m uvicorn promptgate.server:app --host 127.0.0.1 --port "$gateway_port" >/tmp/promptgate-upstream-gateway.log 2>&1 &
gateway_pid="$!"
for _ in {1..60}; do
  curl -fsS "http://127.0.0.1:${gateway_port}/health" >/dev/null 2>&1 && curl -fsS "http://127.0.0.1:${upstream_port}/docs" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS "http://127.0.0.1:${gateway_port}/v1/chat/completions" \
  -H "Authorization: Bearer ${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Email alice@example.com from 10.1.2.3 about Project Raven."}]}' >/dev/null
if grep -F -q -e 'alice@example.com' -e '10.1.2.3' -e 'Project Raven' -e 'fake-upstream-key' "$capture"; then
  echo "FAIL: raw sensitive value or API key reached fake upstream capture" >&2
  cat "$capture" >&2
  exit 1
fi
grep -E -q '\[PRIVATE_EMAIL_[A-Fa-f0-9]{16}\]|\[PRIVATE_EMAIL_001\]' "$capture"
echo "PASS: direct upstream route received rewritten payload only"
