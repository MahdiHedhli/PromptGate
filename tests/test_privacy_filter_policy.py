from promptgate.policy import load_policy
from promptgate.redact import TokenVault, apply_actions
from promptgate.scan.privacy_filter import MockPrivacyFilterProvider, PrivacyFilterHit, scan


def test_policy_actions_apply_to_mocked_privacy_filter_labels():
    policy = load_policy("policies/default.yaml")
    text = "Alice Example"
    findings = scan(text, MockPrivacyFilterProvider([PrivacyFilterHit("private_person", 0, len(text))]))
    result = apply_actions(text, findings, policy, TokenVault())
    assert result.allowed
    assert result.text == "[PRIVATE_PERSON_001]"
