#!/usr/bin/env bash
set -euo pipefail
if ! command -v docker >/dev/null 2>&1; then
  echo "SKIP: docker is required for MITM fake-upstream test"
  exit 0
fi
if [[ -f .env ]]; then set -a; source .env; set +a; fi
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
gateway_port="${PROMPTGATE_MITM_GATEWAY_PORT:-8794}"
proxy_port="${PROMPTGATE_MITM_PROXY_PORT:-8898}"
capture_dir="local/runtime/mitm"
capture_jsonl="${capture_dir}/requests.jsonl"
mkdir -p "$capture_dir"
rm -f "${capture_jsonl}" "${capture_dir}/promptgate-mitm.flows"
gateway_pid=""
cleanup() {
  if [[ -n "$gateway_pid" ]]; then
    kill "$gateway_pid" >/dev/null 2>&1 || true
    wait "$gateway_pid" 2>/dev/null || true
  fi
  COMPOSE_PROJECT_NAME=promptgate_mitm docker compose -f docker-compose.mitm.yml down >/dev/null 2>&1 || true
}
trap cleanup EXIT
compose_build_flag="--build"
if docker image inspect promptgate_mitm-fake-upstream:latest >/dev/null 2>&1; then
  compose_build_flag="--no-build"
fi
COMPOSE_PROJECT_NAME=promptgate_mitm PROMPTGATE_MITM_PROXY_PORT="$proxy_port" docker compose -f docker-compose.mitm.yml up -d "$compose_build_flag" >/tmp/promptgate-mitm-compose.log
for _ in {1..80}; do
  if curl -fsS -x "http://127.0.0.1:${proxy_port}" http://fake-upstream:8791/docs >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done
PROMPTGATE_PROVIDER_MODE=upstream \
PROMPTGATE_UPSTREAM_BASE_URL="http://fake-upstream:8791" \
PROMPTGATE_UPSTREAM_API_KEY="fake-mitm-key" \
PROMPTGATE_UPSTREAM_HTTP_PROXY="http://127.0.0.1:${proxy_port}" \
PROMPTGATE_AUTH_TOKEN="${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}" \
"$py" -m uvicorn promptgate.server:app --host 127.0.0.1 --port "$gateway_port" >/tmp/promptgate-mitm-gateway.log 2>&1 &
gateway_pid="$!"
for _ in {1..60}; do
  curl -fsS "http://127.0.0.1:${gateway_port}/health" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS "http://127.0.0.1:${gateway_port}/v1/chat/completions" \
  -H "Authorization: Bearer ${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Email alice@example.com from 10.1.2.3 about Project Raven."}]}' >/dev/null
blocked_status="$(curl -sS -o /tmp/promptgate-mitm-blocked.json -w "%{http_code}" "http://127.0.0.1:${gateway_port}/v1/chat/completions" \
  -H "Authorization: Bearer ${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}" \
  -H "Content-Type: application/json" \
  -d '{"model":"mock","messages":[{"role":"user","content":"Use sk-test-abc1234567890SECRET in the request."}]}')"
test "$blocked_status" = "400"
sleep 1
test -s "$capture_jsonl"
if grep -F -q -e 'alice@example.com' -e '10.1.2.3' -e 'Project Raven' -e 'sk-test-abc1234567890SECRET' -e 'fake-mitm-key' "$capture_jsonl"; then
  echo "FAIL: raw sensitive value or fake key appeared in MITM capture" >&2
  exit 1
fi
grep -E -q '\[PRIVATE_EMAIL_[A-Fa-f0-9]{16}\]|\[PRIVATE_EMAIL_001\]' "$capture_jsonl"
grep -E -q '\[IP_ADDRESS_[A-Fa-f0-9]{16}\]|\[IP_ADDRESS_001\]' "$capture_jsonl"
grep -E -q '\[CODENAME_[A-Fa-f0-9]{16}\]|\[CODENAME_001\]' "$capture_jsonl"
echo "PASS: MITM fake-upstream capture contains rewritten placeholders and no raw synthetic values"
