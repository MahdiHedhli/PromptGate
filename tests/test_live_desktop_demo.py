import os
import subprocess
from pathlib import Path


def test_live_demo_local_files_are_ignored():
    root = Path(__file__).resolve().parents[1]
    if not (root / ".git").exists():
        gitignore = (root / ".gitignore").read_text(encoding="utf-8")
        assert "local/" in gitignore
        return
    for path in ("local/live-demo.env", "local/live-demo-values.md", "local/runtime/live-demo/requests.jsonl"):
        result = subprocess.run(["git", "check-ignore", "-q", path], cwd=root, check=False)
        assert result.returncode == 0


def test_live_demo_scripts_do_not_echo_provider_secret_values():
    root = Path(__file__).resolve().parents[1]
    scripts = [
        root / "scripts/live-demo-preflight.sh",
        root / "scripts/start-live-demo-stack.sh",
        root / "scripts/live-demo-curl-allowed.sh",
        root / "scripts/live-demo-curl-blocked.sh",
        root / "scripts/assert-live-demo-no-raw-leaks.sh",
    ]
    for script in scripts:
        text = script.read_text(encoding="utf-8")
        assert "echo \"$PROMPTGATE_UPSTREAM_API_KEY" not in text
        assert "echo \"${PROMPTGATE_UPSTREAM_API_KEY" not in text
        assert "set -x" not in text


def test_live_demo_no_raw_leak_assertion_uses_owner_values(tmp_path):
    env_file = tmp_path / "live-demo.env"
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    env_file.write_text(
        "\n".join(
            [
                "DEMO_EMAIL=owner-demo@example.com",
                "DEMO_INTERNAL_IP=10.77.1.8",
                "DEMO_INTERNAL_DOMAIN=api.internal.demo.example",
                    "DEMO_CODENAME='Project Raven'",
                "DEMO_CANARY_SECRET=sk-test-abc1234567890SECRET",
                "PROMPTGATE_UPSTREAM_API_KEY=fake-provider-key",
            ]
        ),
        encoding="utf-8",
    )
    (runtime / "requests.jsonl").write_text('{"body":"Email [PRIVATE_EMAIL_abcdabcdabcdabcd]"}\n', encoding="utf-8")
    env = {**os.environ, "LIVE_DEMO_ENV": str(env_file), "LIVE_DEMO_RUNTIME_DIR": str(runtime)}
    result = subprocess.run(
        ["./scripts/assert-live-demo-no-raw-leaks.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    (runtime / "requests.jsonl").write_text('{"body":"owner-demo@example.com"}\n', encoding="utf-8")
    result = subprocess.run(
        ["./scripts/assert-live-demo-no-raw-leaks.sh"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode != 0
    assert "DEMO_EMAIL" in result.stderr
    assert "owner-demo@example.com" not in result.stderr
