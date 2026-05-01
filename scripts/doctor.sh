#!/usr/bin/env bash
set -euo pipefail
if [[ -f .env ]]; then set -a; source .env; set +a; fi
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3)"; fi
"$py" -m promptgate.cli doctor
