from promptgate.policy import load_policy
from promptgate.redact import TokenVault, apply_actions
from promptgate.scan.findings import Finding


def test_deterministic_tokenization():
    vault = TokenVault()
    assert vault.token_for("private_email", "a@example.com", mode="deterministic") == "[PRIVATE_EMAIL_001]"
    assert vault.token_for("private_email", "a@example.com", mode="deterministic") == "[PRIVATE_EMAIL_001]"


def test_scoped_random_tokens_are_stable_within_conversation_and_isolated():
    vault = TokenVault()
    first = vault.token_for("private_email", "a@example.com", conversation_id="conv-a")
    again = vault.token_for("private_email", "a@example.com", conversation_id="conv-a")
    other = vault.token_for("private_email", "a@example.com", conversation_id="conv-b")
    assert first == again
    assert first != other
    assert first.startswith("[PRIVATE_EMAIL_")
    assert first.endswith("]")


def test_token_restore_is_conversation_scoped_and_unknown_tokens_noop():
    vault = TokenVault()
    token = vault.token_for("private_email", "a@example.com", conversation_id="conv-a")
    assert vault.restore(f"Email {token}", "conv-a") == "Email a@example.com"
    assert vault.restore(f"Email {token}", "conv-b") == f"Email {token}"
    assert vault.restore("Email [PRIVATE_EMAIL_deadbeefdeadbeef]", "conv-a") == "Email [PRIVATE_EMAIL_deadbeefdeadbeef]"


def test_token_ttl_and_lru_eviction():
    now = [1000.0]
    vault = TokenVault(ttl_seconds=10, max_conversations=1, now=lambda: now[0])
    old = vault.token_for("private_email", "old@example.com", conversation_id="old")
    now[0] = 1001.0
    vault.token_for("private_email", "new@example.com", conversation_id="new")
    assert vault.restore(f"Email {old}", "old") == f"Email {old}"
    recent = vault.token_for("private_email", "recent@example.com", conversation_id="recent")
    now[0] = 1012.0
    assert vault.restore(f"Email {recent}", "recent") == f"Email {recent}"


def test_mask_and_tokenize_response():
    policy = load_policy("policies/default.yaml")
    text = "Email alice@example.com or call 212-555-1212"
    findings = [
        Finding("private_email", 6, 23, "alice@example.com", "regex"),
        Finding("private_phone", 32, 44, "212-555-1212", "regex"),
    ]
    result = apply_actions(text, findings, policy, TokenVault())
    assert result.allowed
    assert "alice@example.com" not in result.text
    assert "212-555-1212" not in result.text
    assert "[PRIVATE_EMAIL_" in result.text
    assert "[PRIVATE_PHONE_REDACTED]" in result.text


def test_block_response():
    policy = load_policy("policies/default.yaml")
    result = apply_actions("sk-abc1234567890SECRET", [Finding("api_key", 0, 22, "sk-abc1234567890SECRET", "secrets", "critical")], policy, TokenVault())
    assert not result.allowed
    assert "api_key" in result.blocked_categories


def test_deterministic_mode_can_be_enabled_in_policy():
    policy = load_policy("policies/default.yaml")
    policy.tokenization.mode = "deterministic"
    text = "Email alice@example.com"
    findings = [Finding("private_email", 6, 23, "alice@example.com", "regex")]
    result = apply_actions(text, findings, policy, TokenVault(), conversation_id="conv-a")
    assert result.text == "Email [PRIVATE_EMAIL_001]"


def test_global_audit_only_does_not_rewrite_or_block():
    policy = load_policy("policies/default.yaml")
    policy.audit_only = True
    text = "Use sk-abc1234567890SECRET and email alice@example.com"
    findings = [
        Finding("api_key", 4, 26, "sk-abc1234567890SECRET", "secrets", "critical"),
        Finding("private_email", 37, 54, "alice@example.com", "regex"),
    ]
    result = apply_actions(text, findings, policy, TokenVault(), conversation_id="conv-a")
    assert result.allowed
    assert result.text == text
    assert all(action["audit_only"] for action in result.actions)
    assert "policy_hash" in result.actions[0]
    assert "alice@example.com" not in str(result.actions)


def test_per_rule_audit_only_mixes_with_enforced_rules():
    policy = load_policy("policies/default.yaml")
    policy.rules.append(
        {
            "id": "employee_name",
            "type": "keyword",
            "values": ["Alice Example"],
            "category": "private_person",
            "action": "tokenize",
            "severity": "medium",
            "audit_only": True,
        }
    )
    text = "Alice Example uses sk-abc1234567890SECRET"
    findings = [
        Finding("private_person", 0, 13, "Alice Example", "regex", rule_id="employee_name"),
        Finding("api_key", 19, 41, "sk-abc1234567890SECRET", "secrets", "critical"),
    ]
    result = apply_actions(text, findings, policy, TokenVault(), conversation_id="conv-a")
    assert not result.allowed
    assert "api_key" in result.blocked_categories
    assert any(action["rule_id"] == "employee_name" and action["audit_only"] for action in result.actions)
