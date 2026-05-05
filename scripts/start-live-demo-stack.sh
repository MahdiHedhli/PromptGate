#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env ]]; then
  echo "FAIL: .env is missing" >&2
  exit 1
fi
if [[ ! -f local/live-demo.env ]]; then
  echo "FAIL: local/live-demo.env is missing. Create it from docs/live-demo-values.example.md" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
# shellcheck disable=SC1091
source local/live-demo.env
set +a

[[ -n "${PROMPTGATE_AUTH_TOKEN:-}" ]] || { echo "FAIL: PROMPTGATE_AUTH_TOKEN is not configured" >&2; exit 1; }
[[ "${PROMPTGATE_PROVIDER_MODE:-}" == "upstream" ]] || { echo "FAIL: set PROMPTGATE_PROVIDER_MODE=upstream in local/live-demo.env" >&2; exit 1; }
[[ -n "${PROMPTGATE_UPSTREAM_BASE_URL:-}" ]] || { echo "FAIL: PROMPTGATE_UPSTREAM_BASE_URL is required" >&2; exit 1; }
[[ -n "${PROMPTGATE_UPSTREAM_API_KEY:-}" ]] || { echo "FAIL: PROMPTGATE_UPSTREAM_API_KEY is required" >&2; exit 1; }

py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi

runtime_dir="local/runtime/live-demo"
mitm_ca_dir="$runtime_dir/mitmproxy"
mkdir -p "$runtime_dir" "$mitm_ca_dir"
rm -f "$runtime_dir/requests.jsonl" "$runtime_dir/promptgate-live.flows"

gateway_port="${PROMPTGATE_PORT:-8787}"
proxy_port="${PROMPTGATE_LIVE_MITM_PROXY_PORT:-8899}"
web_port="${PROMPTGATE_LIVE_MITMWEB_PORT:-8897}"
web_password="${PROMPTGATE_LIVE_MITMWEB_PASSWORD:-promptgate-local}"

if lsof -nP -iTCP:"$gateway_port" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "FAIL: 127.0.0.1:${gateway_port} is already in use. Stop the old PromptGate process before starting the live stack." >&2
  lsof -nP -iTCP:"$gateway_port" -sTCP:LISTEN >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  docker rm -f promptgate-live-mitm >/dev/null 2>&1 || true
  docker run -d --name promptgate-live-mitm \
    -p "127.0.0.1:${proxy_port}:8080" \
    -p "127.0.0.1:${web_port}:8081" \
    -v "$PWD/${runtime_dir}:/captures" \
    -v "$PWD/${mitm_ca_dir}:/home/mitmproxy/.mitmproxy" \
    -v "$PWD/scripts/mitm_capture_addon.py:/addons/mitm_capture_addon.py:ro" \
    mitmproxy/mitmproxy:latest \
    mitmweb --web-host 0.0.0.0 --web-port 8081 --listen-host 0.0.0.0 --listen-port 8080 \
      --set block_global=false --set "web_password=${web_password}" \
      -s /addons/mitm_capture_addon.py -w /captures/promptgate-live.flows >/dev/null
else
  echo "FAIL: Docker is required by this helper. Install Docker or start mitmweb manually using docs/DESKTOP_APP_DEMO.md." >&2
  exit 1
fi

mitm_ca_bundle="$PWD/${mitm_ca_dir}/mitmproxy-ca-cert.pem"
for _ in {1..80}; do
  [[ -s "$mitm_ca_bundle" ]] && break
  sleep 0.25
done
if [[ -z "${PROMPTGATE_UPSTREAM_CA_BUNDLE:-}" && -s "$mitm_ca_bundle" ]]; then
  export PROMPTGATE_UPSTREAM_CA_BUNDLE="$mitm_ca_bundle"
fi

PROMPTGATE_UPSTREAM_HTTP_PROXY="http://127.0.0.1:${proxy_port}" \
"$py" -m uvicorn promptgate.server:app --host 127.0.0.1 --port "$gateway_port" >"$runtime_dir/promptgate.log" 2>&1 &
echo "$!" > "$runtime_dir/promptgate.pid"

for _ in {1..80}; do
  curl -fsS "http://127.0.0.1:${gateway_port}/health" >/dev/null 2>&1 && break
  sleep 0.25
done
curl -fsS "http://127.0.0.1:${gateway_port}/health" >/dev/null

echo "PromptGate live demo stack started."
echo "PromptGate: http://127.0.0.1:${gateway_port}"
echo "OpenAI-compatible base URL for Cherry Studio: http://127.0.0.1:${gateway_port}/v1"
echo "mitmweb: http://127.0.0.1:${web_port}"
echo "mitmweb password: ${web_password}"
echo "Local runtime evidence: ${runtime_dir}"
echo "No secrets were printed."
