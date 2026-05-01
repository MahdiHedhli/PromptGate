from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from promptgate.config import current_settings
from promptgate.policy import PolicyValidationError, load_policy

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(prog="promptgate")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument("--industry", default="security_consulting")
    init.add_argument("--enable-secrets", action="store_true")
    init.add_argument("--enable-privacy-filter", choices=["optional", "enabled", "disabled"], default="optional")
    init.add_argument("--no-privacy-filter", action="store_true")
    init.add_argument("--strict", action="store_true")
    init.add_argument("--output", default="policies/default.yaml")
    validate = sub.add_parser("validate-policy")
    validate.add_argument("path")
    sub.add_parser("doctor")
    report = sub.add_parser("report")
    report.add_argument("--output", default="docs/reports/generated/promptgate-report.json")
    bench = sub.add_parser("benchmark")
    bench.add_argument("--iterations", default="3")
    args = parser.parse_args()
    if args.command == "init":
        source = ROOT / "policies" / "industries" / f"{args.industry}.yaml"
        policy = load_policy(source)
        policy.profile = args.industry
        policy.detectors.secrets = True if args.enable_secrets or args.strict else policy.detectors.secrets
        policy.detectors.privacy_filter = False if args.no_privacy_filter else args.enable_privacy_filter
        if args.strict:
            policy.actions["private_email"] = "tokenize"
            policy.actions["private_phone"] = "tokenize"
            policy.actions["file_path"] = "tokenize"
        target = Path(args.output)
        target.parent.mkdir(parents=True, exist_ok=True)
        from promptgate.policy import dump_policy

        dump_policy(policy, target)
        print(f"Wrote {target}")
    elif args.command == "validate-policy":
        try:
            policy = load_policy(args.path)
        except PolicyValidationError as exc:
            print(f"INVALID: {exc}", file=sys.stderr)
            raise SystemExit(1) from exc
        print(f"VALID: {args.path} profile={policy.profile} mode={policy.mode}")
    elif args.command == "doctor":
        raise SystemExit(_doctor())
    elif args.command == "report":
        subprocess.run(["./scripts/export-report.sh"], check=True)
    elif args.command == "benchmark":
        subprocess.run(["./scripts/benchmark-local.py", "--iterations", args.iterations], check=True)


def _doctor() -> int:
    settings = current_settings()
    checks = []
    ok = True
    try:
        policy = load_policy(settings.policy_path)
        checks.append(("policy", "ok", f"profile={policy.profile} raw_prompt_logging={policy.logging.raw_prompts}"))
        if policy.logging.raw_prompts:
            ok = False
            checks.append(("raw_prompt_logging", "warn", "raw prompt logging is enabled"))
    except Exception as exc:
        ok = False
        checks.append(("policy", "fail", str(exc)))
    if settings.unsafe_dev_no_auth:
        ok = False
        checks.append(("auth", "warn", "unsafe dev no-auth mode is enabled"))
    elif settings.local_auth_token:
        checks.append(("auth", "ok", "local auth token configured"))
    else:
        ok = False
        checks.append(("auth", "fail", "PROMPTGATE_AUTH_TOKEN is not configured"))
    if settings.provider_mode == "mock":
        checks.append(("provider", "ok", "mock provider mode"))
    elif settings.provider_mode == "upstream":
        if settings.upstream_base_url and settings.upstream_api_key:
            checks.append(("provider", "ok", f"upstream configured base_url={settings.upstream_base_url} api_key=[redacted]"))
        else:
            ok = False
            checks.append(("provider", "fail", "upstream mode requires base URL and API key"))
    else:
        ok = False
        checks.append(("provider", "fail", f"unknown provider mode {settings.provider_mode}"))
    checks.append(("port", "ok" if _port_available(settings.host, settings.port) else "warn", f"{settings.host}:{settings.port} availability checked"))
    for name, status, detail in checks:
        print(f"{status.upper():5} {name}: {detail}")
    return 0 if ok else 1


def _port_available(host: str, port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        return sock.connect_ex((host, port)) != 0
    finally:
        sock.close()


if __name__ == "__main__":
    main()
