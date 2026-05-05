#!/usr/bin/env bash
set -euo pipefail

branch="$(git branch --show-current 2>/dev/null || echo unknown)"
echo "Branch: ${branch}"
if [[ "$branch" != "main" && "$branch" != "feature/live-desktop-evidence" && "$branch" != "feature/response-token-translation-demo" ]]; then
  echo "WARN: unexpected branch for final desktop demo work"
fi

echo "Working tree:"
git status --short

if [[ ! -f .env ]]; then
  echo "FAIL: .env is missing. Run cp .env.example .env and ./scripts/setup-local-key.sh" >&2
  exit 1
fi
git check-ignore -q .env || { echo "FAIL: .env is not ignored" >&2; exit 1; }

if [[ ! -f local/live-demo.env ]]; then
  echo "WARN: local/live-demo.env is missing. Create it from docs/live-demo-values.example.md"
else
  git check-ignore -q local/live-demo.env || { echo "FAIL: local/live-demo.env is not ignored" >&2; exit 1; }
fi

set -a
# shellcheck disable=SC1091
source .env
if [[ -f local/live-demo.env ]]; then
  # shellcheck disable=SC1091
  source local/live-demo.env
fi
set +a

[[ -n "${PROMPTGATE_AUTH_TOKEN:-}" ]] || { echo "FAIL: PROMPTGATE_AUTH_TOKEN is not configured" >&2; exit 1; }

if [[ "${PROMPTGATE_PROVIDER_MODE:-mock}" != "upstream" ]]; then
  echo "WARN: PROMPTGATE_PROVIDER_MODE is '${PROMPTGATE_PROVIDER_MODE:-mock}', expected upstream for real-provider live demo"
fi
[[ -n "${PROMPTGATE_UPSTREAM_BASE_URL:-}" ]] || echo "WARN: PROMPTGATE_UPSTREAM_BASE_URL is not set"
[[ -n "${PROMPTGATE_UPSTREAM_API_KEY:-}" ]] || echo "WARN: PROMPTGATE_UPSTREAM_API_KEY is not set"

if command -v docker >/dev/null 2>&1; then
  echo "Docker: available"
elif command -v mitmweb >/dev/null 2>&1 || command -v mitmdump >/dev/null 2>&1; then
  echo "mitmproxy: local binary available"
else
  echo "WARN: neither Docker nor mitmproxy binaries were found"
fi

if lsof -nP -iTCP:8787 -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port 8787: in use"
  lsof -nP -iTCP:8787 -sTCP:LISTEN
else
  echo "Port 8787: available"
fi

if curl -fsS http://127.0.0.1:8787/v1/models >/dev/null 2>&1; then
  echo "/v1/models: reachable"
else
  echo "/v1/models: not reachable yet; start PromptGate before configuring the desktop app"
fi

echo "Preflight complete. No secrets were printed."
