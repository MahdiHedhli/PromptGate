#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then set -a; source .env; set +a; fi
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
"$py" -m pytest -q
./scripts/test-egress.sh
./scripts/test-direct-upstream.sh
./scripts/test-litellm-route.sh
./scripts/test-mitm-fake-upstream.sh
./scripts/test-streaming-support.sh
./scripts/benchmark-local.py
./scripts/export-report.sh
./scripts/replay-audit-fixtures.sh
./scripts/assert-no-raw-leaks.sh
./scripts/doctor.sh
"$py" -m promptgate.cli validate-policy policies/default.yaml
echo "PASS: release check completed"
