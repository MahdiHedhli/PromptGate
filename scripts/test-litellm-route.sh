#!/usr/bin/env bash
set -euo pipefail
echo "Testing LiteLLM route using a local fake LiteLLM-compatible upstream."
PROMPTGATE_FAKE_UPSTREAM_PORT="${PROMPTGATE_FAKE_UPSTREAM_PORT:-8792}" ./scripts/test-direct-upstream.sh
echo "PASS: PromptGate -> local fake LiteLLM/provider route received rewritten payload only"
