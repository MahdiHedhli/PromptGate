#!/usr/bin/env bash
set -euo pipefail
py="${PYTHON:-}"
if [[ -z "$py" && -x ".venv/bin/python" ]]; then py=".venv/bin/python"; fi
if [[ -z "$py" ]]; then py="$(command -v python3.12 || command -v python3.11 || command -v python3)"; fi
"$py" - <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path

from promptgate.gateway import process_payload
from promptgate.policy import load_policy
from promptgate.redact import TokenVault

policy = load_policy("policies/default.yaml")
cases = [
    ("benign", {"model": "mock", "messages": [{"role": "user", "content": "Summarize public docs."}]}),
    ("pii", {"model": "mock", "messages": [{"role": "user", "content": "Contact alice@example.com from 10.1.2.3 about Project Raven."}]}),
    ("secret", {"model": "mock", "messages": [{"role": "user", "content": "Use OPENAI_API_KEY=sk-abc1234567890SECRET in the demo."}]}),
]
out = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "policy_profile": policy.profile,
    "mode": policy.mode,
    "detectors": policy.detectors.__dict__,
    "upstream_mode": "mock",
    "cases": [],
}
for name, payload in cases:
    result = process_payload(payload, policy, TokenVault())
    out["cases"].append(
        {
            "name": name,
            "allowed": result.allowed,
            "blocked_categories": result.blocked_categories,
            "findings": result.audit,
            "timings": result.timings,
            "redacted_payload": result.payload if result.allowed else "[blocked locally]",
        }
    )
Path("docs/reports/generated").mkdir(parents=True, exist_ok=True)
json_path = Path("docs/reports/generated/promptgate-report.json")
md_path = Path("docs/reports/generated/promptgate-report.md")
json_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
lines = [
    "# PromptGate Redacted Report",
    "",
    f"- Generated: {out['generated_at']}",
    f"- Policy profile: {out['policy_profile']}",
    f"- Mode: {out['mode']}",
    f"- Upstream mode: {out['upstream_mode']}",
    "",
    "| Case | Allowed | Blocked Categories | Findings | Total ms |",
    "|---|---:|---|---:|---:|",
]
for case in out["cases"]:
    lines.append(
        f"| {case['name']} | {case['allowed']} | {', '.join(case['blocked_categories']) or '-'} | "
        f"{len(case['findings'])} | {case['timings']['total_ms']} |"
    )
md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Wrote {json_path} and {md_path}")
PY
