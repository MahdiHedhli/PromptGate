from pathlib import Path

import pytest
import yaml

from promptgate.cli import main
from promptgate.policy import PolicyValidationError, load_policy


def test_policy_loading():
    policy = load_policy("policies/default.yaml")
    assert policy.profile == "security_consulting"
    assert policy.action_for("api_key") == "block"
    assert policy.logging.raw_prompts is False


def test_industry_policy_generation(tmp_path, monkeypatch):
    output = tmp_path / "finance.yaml"
    monkeypatch.setattr("sys.argv", ["promptgate", "init", "--industry", "finance", "--strict", "--output", str(output)])
    main()
    policy = load_policy(output)
    assert policy.profile == "finance"
    assert policy.actions["private_phone"] == "tokenize"
    assert Path(output).exists()


def _write_policy(tmp_path, patch):
    with open("policies/default.yaml", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    for key, value in patch.items():
        data[key] = value
    path = tmp_path / "policy.yaml"
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def test_invalid_policy_missing_required_section(tmp_path):
    path = _write_policy(tmp_path, {"actions": None})
    with pytest.raises(PolicyValidationError, match="actions must be a mapping"):
        load_policy(path)


def test_invalid_policy_duplicate_rule_ids(tmp_path):
    path = _write_policy(
        tmp_path,
        {
            "rules": [
                {"id": "dupe", "type": "keyword", "values": ["A"], "action": "tokenize", "severity": "low"},
                {"id": "dupe", "type": "keyword", "values": ["B"], "action": "mask", "severity": "medium"},
            ]
        },
    )
    with pytest.raises(PolicyValidationError, match="duplicate rule id.*dupe"):
        load_policy(path)


def test_invalid_policy_bad_regex_mentions_rule_id(tmp_path):
    path = _write_policy(tmp_path, {"rules": [{"id": "bad_regex", "type": "regex", "pattern": "(", "action": "tokenize", "severity": "high"}]})
    with pytest.raises(PolicyValidationError, match="bad_regex"):
        load_policy(path)


def test_invalid_policy_unknown_action(tmp_path):
    path = _write_policy(tmp_path, {"actions": {"private_email": "scrub"}})
    with pytest.raises(PolicyValidationError, match="unknown action 'scrub'"):
        load_policy(path)


def test_invalid_policy_profile(tmp_path):
    path = _write_policy(tmp_path, {"profile": "unknown_industry"})
    with pytest.raises(PolicyValidationError, match="invalid industry profile"):
        load_policy(path)


def test_invalid_privacy_filter_config(tmp_path):
    path = _write_policy(tmp_path, {"detectors": {"regex": True, "secrets": True, "privacy_filter": "maybe", "normalization": True, "sample_dlp_imports": True}})
    with pytest.raises(PolicyValidationError, match="invalid privacy_filter"):
        load_policy(path)
