#!/usr/bin/env bash
set -euo pipefail
src="$(pwd)"
tmp="$(mktemp -d)"
cleanup() { rm -rf "$tmp"; }
trap cleanup EXIT
rsync -a \
  --exclude='.git' \
  --exclude='.venv' \
  --exclude='.env' \
  --include='.env.example' \
  --exclude='.env.*' \
  --exclude='__pycache__' \
  --exclude='.pytest_cache' \
  --exclude='docs/reports/generated' \
  --exclude='docs/reports/benchmarks' \
  "$src/" "$tmp/PromptGate/"
cd "$tmp/PromptGate"
py="$(command -v python3.12 || command -v python3)"
"$py" -m venv .venv
.venv/bin/python -m pip install -e '.[dev]' >/tmp/promptgate-smoke-pip.log
cp .env.example .env
./scripts/setup-local-key.sh >/tmp/promptgate-smoke-key.log
tmp_port="8878"
sed "s/^PROMPTGATE_PORT=.*/PROMPTGATE_PORT=${tmp_port}/" .env > .env.tmp && mv .env.tmp .env
./scripts/init-policy.sh security_consulting
.venv/bin/python -m pytest -q
./scripts/test-egress.sh
if command -v docker >/dev/null 2>&1 && ! lsof -iTCP:8787 -sTCP:LISTEN >/dev/null 2>&1; then
  docker compose up -d --build >/tmp/promptgate-smoke-docker.log
  sleep 1
  curl -fsS http://127.0.0.1:8787/health >/dev/null
  docker compose down >/tmp/promptgate-smoke-docker-down.log
elif command -v docker >/dev/null 2>&1; then
  echo "SKIP: Docker smoke path skipped because 127.0.0.1:8787 is already in use"
fi
echo "PASS: clean install smoke test completed in $tmp/PromptGate"
