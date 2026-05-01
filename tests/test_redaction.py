from promptgate.policy import load_policy
from promptgate.redact import TokenVault, apply_actions
from promptgate.scan.findings import Finding


def test_deterministic_tokenization():
    vault = TokenVault()
    assert vault.token_for("private_email", "a@example.com") == "[PRIVATE_EMAIL_001]"
    assert vault.token_for("private_email", "a@example.com") == "[PRIVATE_EMAIL_001]"


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
    assert "[PRIVATE_EMAIL_001]" in result.text
    assert "[PRIVATE_PHONE_REDACTED]" in result.text


def test_block_response():
    policy = load_policy("policies/default.yaml")
    result = apply_actions("sk-abc1234567890SECRET", [Finding("api_key", 0, 22, "sk-abc1234567890SECRET", "secrets", "critical")], policy, TokenVault())
    assert not result.allowed
    assert "api_key" in result.blocked_categories
