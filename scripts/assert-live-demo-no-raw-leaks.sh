#!/usr/bin/env bash
set -euo pipefail

env_file="${LIVE_DEMO_ENV:-local/live-demo.env}"
runtime_dir="${LIVE_DEMO_RUNTIME_DIR:-local/runtime/live-demo}"

if [[ ! -f "$env_file" ]]; then
  echo "FAIL: ${env_file} is missing" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source "$env_file"
set +a

targets=("$runtime_dir/requests.jsonl" "$runtime_dir/promptgate.log")
needles=(DEMO_EMAIL DEMO_INTERNAL_IP DEMO_INTERNAL_DOMAIN DEMO_CODENAME DEMO_CANARY_SECRET PROMPTGATE_UPSTREAM_API_KEY)

for target in "${targets[@]}"; do
  [[ -f "$target" ]] || continue
  for key in "${needles[@]}"; do
    value="${!key:-}"
    [[ -n "$value" ]] || continue
    if grep -F -q -- "$value" "$target"; then
      echo "FAIL: raw live demo value for ${key} appeared in ${target}" >&2
      exit 1
    fi
  done
done

echo "PASS: no raw live demo values found in MITM capture or PromptGate log."
