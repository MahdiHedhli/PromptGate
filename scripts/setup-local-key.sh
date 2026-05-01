#!/usr/bin/env bash
set -euo pipefail
env_file="${1:-.env}"
py_for_key="$(command -v python3.12 || command -v python3.11 || command -v python3)"
key="$("$py_for_key" - <<'PY'
import secrets
import string
alphabet = string.ascii_letters + string.digits
print("".join(secrets.choice(alphabet) for _ in range(40)))
PY
)"
if [[ ! -f "$env_file" ]]; then
  cp .env.example "$env_file"
fi
if grep -q '^PROMPTGATE_AUTH_TOKEN=' "$env_file"; then
  backup="${env_file}.bak.$(date +%Y%m%d%H%M%S)"
  cp "$env_file" "$backup"
  tmp="$(mktemp)"
  sed "s/^PROMPTGATE_AUTH_TOKEN=.*/PROMPTGATE_AUTH_TOKEN=${key}/" "$env_file" > "$tmp"
  mv "$tmp" "$env_file"
  echo "Backed up existing config to ${backup}"
else
  printf '\nPROMPTGATE_AUTH_TOKEN=%s\n' "$key" >> "$env_file"
fi
echo "Wrote local PromptGate key to ${env_file}"
