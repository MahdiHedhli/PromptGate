#!/usr/bin/env bash
set -euo pipefail

install=false
with_cherry=false
with_mitm=false

for arg in "$@"; do
  case "$arg" in
    --install) install=true ;;
    --with-cherry-studio) with_cherry=true ;;
    --with-mitmproxy) with_mitm=true ;;
    -h|--help)
      cat <<'EOF'
Usage: ./scripts/install-demo-deps.sh [--install] [--with-cherry-studio] [--with-mitmproxy]

Default mode is check-only. It prints missing dependencies and suggested
commands without changing the system.

--install             Install safe CLI/project dependencies only.
--with-cherry-studio  Also install Cherry Studio with Homebrew cask.
--with-mitmproxy      Also install local mitmproxy with Homebrew.

Docker is preferred for MITM because it avoids a host Python/tool install.
Provider credentials and live demo values are never installed by this script.
EOF
      exit 0
      ;;
    *)
      echo "FAIL: unknown argument: $arg" >&2
      exit 1
      ;;
  esac
done

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

echo "PromptGate demo dependency check"
echo "Repo: $root"

missing=()

check_cmd() {
  local name="$1"
  local cmd="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "OK: $name"
  else
    echo "MISSING: $name"
    missing+=("$name")
  fi
}

check_cmd "git" git
check_cmd "curl" curl
check_cmd "lsof" lsof
check_cmd "python3.11 or newer" python3.11 || true
if ! command -v python3.11 >/dev/null 2>&1 && ! command -v python3.12 >/dev/null 2>&1 && ! command -v python3 >/dev/null 2>&1; then
  missing+=("python")
fi

if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    echo "OK: Docker CLI and daemon"
  else
    echo "MISSING: Docker daemon is not reachable"
    missing+=("docker-daemon")
  fi
else
  echo "MISSING: Docker CLI"
  missing+=("docker")
fi

if command -v brew >/dev/null 2>&1; then
  echo "OK: Homebrew"
else
  echo "MISSING: Homebrew"
  missing+=("homebrew")
fi

if mdfind "kMDItemFSName == '*Cherry*Studio*' || kMDItemDisplayName == '*Cherry*Studio*'" 2>/dev/null | grep -qi "Cherry"; then
  echo "OK: Cherry Studio appears installed"
elif find /Applications "$HOME/Applications" -maxdepth 2 \( -iname '*cherry*studio*' -o -iname '*cherrystudio*' \) 2>/dev/null | grep -qi "cherry"; then
  echo "OK: Cherry Studio appears installed"
else
  echo "MISSING: Cherry Studio desktop app"
  missing+=("cherry-studio")
fi

if [[ -x ".venv/bin/python" ]]; then
  echo "OK: .venv"
else
  echo "MISSING: .venv"
  missing+=("venv")
fi

if [[ -f ".env" ]]; then
  echo "OK: .env exists"
else
  echo "MISSING: .env"
  missing+=(".env")
fi

if [[ -f "local/live-demo.env" ]]; then
  echo "OK: local/live-demo.env exists"
else
  echo "MISSING: local/live-demo.env"
  missing+=("live-demo-env")
fi

if [[ "$install" != true ]]; then
  cat <<'EOF'

Check-only mode complete. To install project-local dependencies:

  ./scripts/install-demo-deps.sh --install

Owner-only/manual items:

  - Provider credentials in local/live-demo.env
  - Cherry Studio GUI configuration
  - Real-provider MITM visual verification

Optional GUI/tool installs:

  brew install --cask cherry-studio
  brew install mitmproxy

Docker is preferred for MITM, so local mitmproxy is optional.
EOF
  exit 0
fi

py=""
if command -v python3.12 >/dev/null 2>&1; then
  py="$(command -v python3.12)"
elif command -v python3.11 >/dev/null 2>&1; then
  py="$(command -v python3.11)"
elif command -v python3 >/dev/null 2>&1; then
  py="$(command -v python3)"
else
  echo "FAIL: Python 3.11+ is required before project dependencies can be installed." >&2
  exit 1
fi

if [[ ! -d ".venv" ]]; then
  "$py" -m venv .venv
fi
.venv/bin/python -m pip install -e ".[dev]"

if [[ ! -f ".env" ]]; then
  cp .env.example .env
fi
if ! grep -q '^PROMPTGATE_AUTH_TOKEN=' .env; then
  ./scripts/setup-local-key.sh
fi

mkdir -p local
if [[ ! -f "local/live-demo.env" ]]; then
  cat > local/live-demo.env <<'EOF'
# Fill this file with owner-only values before the live desktop demo.
# Use docs/live-demo-values.example.md as the reference.
PROMPTGATE_PROVIDER_MODE=upstream
PROMPTGATE_MODEL_LIST=promptgate-live
PROVIDER_MODEL=promptgate-live
EOF
  echo "Wrote placeholder local/live-demo.env. Fill provider credentials and demo values before running the live demo."
fi

if [[ "$with_cherry" == true ]]; then
  command -v brew >/dev/null 2>&1 || { echo "FAIL: Homebrew is required for --with-cherry-studio" >&2; exit 1; }
  brew install --cask cherry-studio
fi

if [[ "$with_mitm" == true ]]; then
  command -v brew >/dev/null 2>&1 || { echo "FAIL: Homebrew is required for --with-mitmproxy" >&2; exit 1; }
  brew install mitmproxy
fi

echo "Dependency setup complete. No provider credentials were printed."
