#!/usr/bin/env bash
set -euo pipefail

echo "NOTE: streaming is supported now; running test-streaming-support.sh"
exec "$(dirname "$0")/test-streaming-support.sh"
