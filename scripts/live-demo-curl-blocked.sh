#!/usr/bin/env bash
set -euo pipefail

set -a
[[ -f .env ]] && source .env
[[ -f local/live-demo.env ]] && source local/live-demo.env
set +a

required=(PROMPTGATE_AUTH_TOKEN DEMO_CANARY_SECRET DEMO_PROMPT_CONTEXT)
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
before_count=0
if [[ -f "$runtime_dir/requests.jsonl" ]]; then
  before_count="$(wc -l < "$runtime_dir/requests.jsonl" | tr -d ' ')"
fi

prompt="I'm reviewing PromptGate before publishing.

Context from the real repo:
${DEMO_PROMPT_CONTEXT}

Do not process this fake canary secret: ${DEMO_CANARY_SECRET}"

.venv/bin/python - <<'PY' "$runtime_dir/blocked-request.json" "$model" "$prompt"
import json, sys
path, model, prompt = sys.argv[1:]
payload = {"model": model, "stream": False, "messages": [{"role": "user", "content": prompt}]}
open(path, "w", encoding="utf-8").write(json.dumps(payload))
PY

status="$(curl -sS -o "$runtime_dir/blocked-response.json" -w "%{http_code}" "http://127.0.0.1:${port}/v1/chat/completions" \
  -H "Authorization: Bearer ${PROMPTGATE_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "@${runtime_dir}/blocked-request.json")"

if [[ "$status" != "400" ]]; then
  echo "FAIL: blocked live demo prompt expected HTTP 400, got ${status}" >&2
  exit 1
fi

after_count="$before_count"
if [[ -f "$runtime_dir/requests.jsonl" ]]; then
  after_count="$(wc -l < "$runtime_dir/requests.jsonl" | tr -d ' ')"
fi
if [[ "$after_count" != "$before_count" ]]; then
  echo "FAIL: blocked prompt appears to have created an upstream MITM request" >&2
  exit 1
fi
echo "PASS: canary secret prompt was blocked before upstream egress."
