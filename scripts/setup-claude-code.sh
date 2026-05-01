#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
port="${PROMPTGATE_PORT:-8787}"
token="${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}"
cat <<EOF
export ANTHROPIC_AUTH_TOKEN=${token}
export ANTHROPIC_BASE_URL=http://127.0.0.1:${port}

# OpenAI-compatible smoke request:
curl -s http://127.0.0.1:${port}/v1/chat/completions \\
  -H "Authorization: Bearer ${token}" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"mock","messages":[{"role":"user","content":"hello from PromptGate"}]}'
EOF
