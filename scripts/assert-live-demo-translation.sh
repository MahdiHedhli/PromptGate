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

off_response="$runtime_dir/allowed-response-off.json"
on_response="$runtime_dir/allowed-response-on.json"
capture="$runtime_dir/requests.jsonl"

for path in "$off_response" "$on_response" "$capture"; do
  if [[ ! -f "$path" ]]; then
    echo "FAIL: expected ${path}. Run live-demo-curl-allowed.sh for both modes first." >&2
    exit 1
  fi
done

raw_values=("${DEMO_EMAIL:-}" "${DEMO_INTERNAL_IP:-}" "${DEMO_INTERNAL_DOMAIN:-}" "${DEMO_CODENAME:-}")

if ! grep -E -q '\[(PRIVATE_EMAIL|IP_ADDRESS|DOMAIN|CODENAME)_[A-Za-z0-9]+' "$off_response"; then
  echo "FAIL: translation OFF response did not contain PromptGate placeholders" >&2
  exit 1
fi

for value in "${raw_values[@]}"; do
  [[ -n "$value" ]] || continue
  if ! grep -F -q -- "$value" "$on_response"; then
    echo "FAIL: translation ON response did not restore expected controlled value" >&2
    exit 1
  fi
  if grep -F -q -- "$value" "$capture"; then
    echo "FAIL: raw controlled value appeared in MITM upstream capture" >&2
    exit 1
  fi
done

if ! grep -E -q '\[(PRIVATE_EMAIL|IP_ADDRESS|DOMAIN|CODENAME)_[A-Za-z0-9]+' "$capture"; then
  echo "FAIL: MITM upstream capture did not contain PromptGate placeholders" >&2
  exit 1
fi

echo "PASS: translation OFF shows placeholders, translation ON restores local values, and MITM upstream capture stays tokenized."
