#!/usr/bin/env bash
set -euo pipefail
industry="${1:-security_consulting}"
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
"$py" -m promptgate.cli init --industry "$industry" --enable-secrets --output policies/default.yaml
