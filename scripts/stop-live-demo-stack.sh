#!/usr/bin/env bash
set -euo pipefail

runtime_dir="local/runtime/live-demo"
if [[ -f "$runtime_dir/promptgate.pid" ]]; then
  pid="$(cat "$runtime_dir/promptgate.pid")"
  kill "$pid" >/dev/null 2>&1 || true
  rm -f "$runtime_dir/promptgate.pid"
fi

if command -v docker >/dev/null 2>&1; then
  docker rm -f promptgate-live-mitm >/dev/null 2>&1 || true
fi

if [[ "${1:-}" == "--delete-evidence" ]]; then
  rm -rf "$runtime_dir"
  echo "Stopped live demo stack and deleted local runtime evidence."
else
  echo "Stopped live demo stack. Local evidence remains under ${runtime_dir}."
fi
