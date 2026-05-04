from pathlib import Path


def test_demo_dependency_script_is_safe_by_default():
    script = Path("scripts/install-demo-deps.sh").read_text(encoding="utf-8")
    assert "Default mode is check-only" in script
    assert "brew install --cask cherry-studio" in script
    assert "--with-cherry-studio" in script
    assert "PROMPTGATE_UPSTREAM_API_KEY" not in script
    assert "set -x" not in script
