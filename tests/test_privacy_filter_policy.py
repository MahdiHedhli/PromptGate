from promptgate.policy import load_policy
from promptgate.redact import TokenVault, apply_actions
from promptgate.scan.privacy_filter import LocalServicePrivacyFilterProvider, MockPrivacyFilterProvider, PrivacyFilterHit, scan


def test_policy_actions_apply_to_mocked_privacy_filter_labels():
    policy = load_policy("policies/default.yaml")
    text = "Alice Example"
    findings = scan(text, MockPrivacyFilterProvider([PrivacyFilterHit("private_person", 0, len(text))]))
    result = apply_actions(text, findings, policy, TokenVault())
    assert result.allowed
    assert result.text.startswith("[PRIVATE_PERSON_")
    assert result.text.endswith("]")
    assert text not in result.text


def test_local_service_privacy_filter_provider(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"findings": [{"label": "private_email", "start": 6, "end": 23, "score": 0.99}]}

    def fake_post(url, json, timeout):
        assert url == "http://privacy-filter.local/scan"
        assert json == {"text": "Email alice@example.com"}
        assert timeout == 1.5
        return FakeResponse()

    monkeypatch.setattr("httpx.post", fake_post)
    provider = LocalServicePrivacyFilterProvider("http://privacy-filter.local", timeout_seconds=1.5)
    findings = scan("Email alice@example.com", provider)
    assert findings[0].category == "private_email"
    assert findings[0].detector == "privacy_filter"
