#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
port="${PROMPTGATE_PORT:-8787}"
cat <<EOF
# Load the local PromptGate key without printing it.
if [ -f .env ]; then set -a; . ./.env; set +a; fi
export ANTHROPIC_AUTH_TOKEN="\${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}"
export ANTHROPIC_BASE_URL=http://127.0.0.1:${port}

# OpenAI-compatible smoke request:
curl -s http://127.0.0.1:${port}/v1/chat/completions \\
  -H "Authorization: Bearer \${PROMPTGATE_AUTH_TOKEN:-local_promptgate_key}" \\
  -H "Content-Type: application/json" \\
  -d '{"model":"mock","messages":[{"role":"user","content":"hello from PromptGate"}]}'
EOF
