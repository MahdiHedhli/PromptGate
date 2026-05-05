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
translation="off"
if [[ "${1:-}" == "--translate" ]]; then
  translation="${2:-}"
fi
case "$translation" in
  off) model="promptgate-live" ;;
  on) model="promptgate-live-translate" ;;
  *) echo "FAIL: use --translate off or --translate on" >&2; exit 1 ;;
esac

prompt="I am testing a local AI DLP gateway called PromptGate.

Use the exact values I provide below when summarizing. Do not invent replacements.

Context from the real repo:
${DEMO_PROMPT_CONTEXT}

Task:
1. Summarize the finding in two sentences.
2. Include the server IP, internal domain, project codename, and owner email exactly as shown in your input.

Controlled demo values:
- Owner email: ${DEMO_EMAIL}
- Internal domain: ${DEMO_INTERNAL_DOMAIN}
- Server IP: ${DEMO_INTERNAL_IP}
- Project codename: ${DEMO_CODENAME}"

.venv/bin/python - <<'PY' "$runtime_dir/allowed-request-${translation}.json" "$model" "$prompt"
import json, sys
path, model, prompt = sys.argv[1:]
payload = {"model": model, "stream": False, "messages": [{"role": "user", "content": prompt}]}
open(path, "w", encoding="utf-8").write(json.dumps(payload))
PY

status="$(curl -sS -o "$runtime_dir/allowed-response-${translation}.json" -w "%{http_code}" "http://127.0.0.1:${port}/v1/chat/completions" \
  -H "Authorization: Bearer ${PROMPTGATE_AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary "@${runtime_dir}/allowed-request-${translation}.json")"

if [[ "$status" != "200" ]]; then
  echo "FAIL: allowed live demo prompt returned HTTP ${status}" >&2
  exit 1
fi
echo "PASS: allowed live demo prompt completed with translation ${translation}. Evidence written under ${runtime_dir}."
