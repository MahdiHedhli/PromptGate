#!/usr/bin/env bash
set -euo pipefail
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3)"; fi
"$py" - <<'PY'
import json
from pathlib import Path

from promptgate.gateway import process_payload
from promptgate.policy import load_policy
from promptgate.redact import TokenVault

policy = load_policy("policies/default.yaml")
failures = []
for path in sorted(Path("tests/fixtures/replay").glob("*.json")):
    fixture = json.loads(path.read_text(encoding="utf-8"))
    result = process_payload(fixture["payload"], policy, TokenVault())
    payload_body = json.dumps(result.payload) if result.allowed else ""
    body = payload_body + json.dumps(result.audit) + json.dumps(result.blocked_categories)
    if result.allowed != fixture["expect_allowed"]:
        failures.append(f"{path}: expected allowed={fixture['expect_allowed']} got {result.allowed}")
    for value in fixture.get("must_not_contain", []):
        if value in body:
            failures.append(f"{path}: leaked forbidden value {value}")
    for value in fixture.get("must_contain", []):
        if value not in body:
            failures.append(f"{path}: missing expected marker {value}")
if failures:
    raise SystemExit("\n".join(failures))
print("PASS: replay audit fixtures matched expected allow/block/rewrite outcomes")
PY
