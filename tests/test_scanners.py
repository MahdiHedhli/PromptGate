from promptgate.scan import normalize, regex, secrets
from promptgate.scan.privacy_filter import MockPrivacyFilterProvider, PrivacyFilterHit, scan as privacy_scan


def test_regex_scanner():
    findings = regex.scan("Contact alice@example.com from 10.1.2.3 and api.internal.corp.example")
    categories = {f.category for f in findings}
    assert "private_email" in categories
    assert "ip_address" in categories
    assert "internal_domain" in categories


def test_secret_scanner():
    findings = secrets.scan("OPENAI_API_KEY=sk-abc1234567890SECRET")
    assert any(f.category in {"secret", "api_key"} for f in findings)


def test_normalization_scanner_blocks_uncertain_span():
    findings = normalize.scan("j0hn d0e at ex@mpl3 dot com")
    assert findings
    assert findings[0].normalized is True
    assert findings[0].safe_replace is False


def test_privacy_filter_mocked_findings():
    provider = MockPrivacyFilterProvider([PrivacyFilterHit("private_person", 0, 5)])
    findings = privacy_scan("Alice called", provider)
    assert findings[0].category == "private_person"
