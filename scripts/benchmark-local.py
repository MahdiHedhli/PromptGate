#!/usr/bin/env python3.12
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and not os.environ.get("VIRTUAL_ENV") and sys.prefix == sys.base_prefix:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

sys.path.insert(0, str(ROOT))

from promptgate.gateway import process_payload
from promptgate.policy import load_policy
from promptgate.redact import TokenVault


CASES = {
    "benign_small": "Summarize public release notes.",
    "pii_small": "Email alice@example.com from 10.1.2.3 about Project Raven.",
    "secret_small": "Use OPENAI_API_KEY=sk-abc1234567890SECRET in the sample.",
    "obfuscated_small": "Reach me at alice at example dot com from api dot internal dot corp dot example dot com.",
    "benign_medium": "Summarize this public architecture note. " * 80,
    "pii_medium": ("Customer alice@example.com called from 212-555-1212 about Project Raven. " * 60),
    "secret_medium": ("Review logs. " * 40) + "DATABASE_URL=postgres://user:pass@db.internal.local:5432/app",
    "obfuscated_medium": ("Signal: a-l-i-c-e at example dot com and sk-abc 123 456 789 SECRET. " * 20),
    "benign_large": "Public docs and implementation notes. " * 500,
    "pii_large": ("alice@example.com 10.1.2.3 Project Raven " * 180),
    "secret_large": ("normal context " * 500) + " sk-abc1234567890SECRET",
    "obfuscated_large": ("api dot internal dot corp dot example dot com " * 150),
    "tool_output_medium": "Tool returned owner alice@example.com from 10.1.2.3. " * 40,
    "json_string_medium": '{"email":"alice@example.com","host":"api.internal.corp.example.com","note":"Project Raven"}',
    "nested_content_medium": "Nested content block with alice@example.com and /Users/alice/project/.env",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", default="policies/default.yaml")
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--out-dir", default="docs/reports/benchmarks")
    args = parser.parse_args()

    policy = load_policy(args.policy)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, text in CASES.items():
        timings = []
        allowed_values = []
        finding_counts = []
        stage_timings = []
        for _ in range(args.iterations):
            payload = _payload_for(name, text)
            started = time.perf_counter()
            result = process_payload(payload, policy, TokenVault())
            timings.append((time.perf_counter() - started) * 1000)
            allowed_values.append(result.allowed)
            finding_counts.append(len(result.audit))
            stage_timings.append(result.timings)
        rows.append(
            {
                "case": name,
                "bytes": len(text.encode("utf-8")),
                "allowed": all(allowed_values),
                "blocked": not any(allowed_values),
                "findings_median": statistics.median(finding_counts),
                "total_ms_median": round(statistics.median(timings), 3),
                "total_ms_max": round(max(timings), 3),
                "extract_ms_median": round(statistics.median(t["extract_ms"] for t in stage_timings), 3),
                "scan_ms_median": round(statistics.median(t["scan_ms"] for t in stage_timings), 3),
                "decision_rewrite_ms_median": round(statistics.median(t["decision_rewrite_ms"] for t in stage_timings), 3),
            }
        )

    json_path = out_dir / "latest.json"
    summary_path = out_dir / "latest.md"
    json_path.write_text(json.dumps({"iterations": args.iterations, "cases": rows}, indent=2), encoding="utf-8")
    summary_path.write_text(_summary(rows), encoding="utf-8")
    print(_summary(rows))
    print(f"\nWrote {json_path} and {summary_path}")


def _summary(rows: list[dict]) -> str:
    lines = [
        "# PromptGate Local Benchmark",
        "",
        "| Case | Bytes | Allowed | Blocked | Median Findings | Extract ms | Scan ms | Rewrite ms | Total ms | Max ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['case']} | {row['bytes']} | {row['allowed']} | {row['blocked']} | "
            f"{row['findings_median']} | {row['extract_ms_median']} | {row['scan_ms_median']} | "
            f"{row['decision_rewrite_ms_median']} | {row['total_ms_median']} | {row['total_ms_max']} |"
        )
    return "\n".join(lines)


def _payload_for(name: str, text: str) -> dict:
    if name == "tool_output_medium":
        return {"model": "mock", "messages": [{"role": "tool", "content": text}]}
    if name == "json_string_medium":
        return {"model": "mock", "messages": [{"role": "assistant", "tool_calls": [{"function": {"name": "lookup", "arguments": text}}]}]}
    if name == "nested_content_medium":
        return {"model": "mock", "input": [{"role": "user", "content": [{"type": "input_text", "text": text}]}]}
    return {"model": "mock", "messages": [{"role": "user", "content": text}]}


if __name__ == "__main__":
    main()
