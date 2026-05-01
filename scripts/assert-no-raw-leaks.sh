#!/usr/bin/env bash
set -euo pipefail
targets=(
  "docs/reports/benchmarks"
  "docs/reports/generated"
)
needles=(
  "sk-abc1234567890SECRET"
  "OPENAI_API_KEY=sk-abc1234567890SECRET"
  "alice@example.com"
  "10.1.2.3"
  "Project Raven"
  "Bearer upstream-secret"
  "upstream-secret"
)
for target in "${targets[@]}"; do
  [[ -e "$target" ]] || continue
  for needle in "${needles[@]}"; do
    if grep -R -F -q -- "$needle" "$target"; then
      echo "FAIL: raw sensitive value found in runtime artifact target=$target value=$needle" >&2
      exit 1
    fi
  done
done
echo "PASS: no raw synthetic secrets found in runtime reports"
