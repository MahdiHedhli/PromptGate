#!/usr/bin/env bash
set -euo pipefail

set -a
[[ -f .env ]] && source .env
[[ -f local/live-demo.env ]] && source local/live-demo.env
set +a

required=(PROMPTGATE_AUTH_TOKEN DEMO_EMAIL DEMO_INTERNAL_IP DEMO_INTERNAL_DOMAIN DEMO_CODENAME DEMO_PROMPT_CONTEXT)
for key in "${required[@]}"; do
  if [[ -z "${!key:-}" ]]; then
    echo "FAIL: ${key} is not configured. See docs/live-demo-values.example.md" >&2
    exit 1
  fi
done

runtime_dir="local/runtime/live-demo"
mkdir -p "$runtime_dir"
port="${PROMPTGATE_PORT:-8787}"
model="${PROVIDER_MODEL:-promptgate-live}"

prompt="I'm reviewing this PromptGate policy and threat model excerpt before publishing the MVP.

Context from the real repo:
${DEMO_PROMPT_CONTEXT}

Please summarize the risk and suggest what to test next.

Operational details from my local demo environment:
- Contact: ${DEMO_EMAIL}
- Internal service: ${DEMO_INTERNAL_DOMAIN}
- Internal IP: ${DEMO_INTERNAL_IP}
- Project codename: ${DEMO_CODENAME}"

.venv/bin/python - <<'PY' "$runtime_dir/allowed-request.json" "$model" "$prompt"
import json, sys
path, model, prompt = sys.argv[1:]
payload = {"model": model, "stream": False, "messages": [{"role": "user", "content": prompt}]}
open(path, "w", encoding="utf-8").write(json.dumps(payload))
PY

status="$(curl -sS -o "$runtime_dir/allowed-response.json" -w "%{http_code}" "http://127.0.0.1:${port}/v1/chat/completions" \
  -H "Authorization: Bearer ${PROMPTGATE_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "@${runtime_dir}/allowed-request.json")"

if [[ "$status" != "200" ]]; then
  echo "FAIL: allowed live demo prompt returned HTTP ${status}" >&2
  exit 1
fi
echo "PASS: allowed live demo prompt completed. Evidence written under ${runtime_dir}."
