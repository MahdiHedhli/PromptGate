from __future__ import annotations

import re

from promptgate.scan.findings import Finding

SECRET_PATTERNS = [
    ("secret", r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----[\s\S]+?-----END (?:RSA |EC |OPENSSH |)PRIVATE KEY-----", "critical"),
    ("jwt", r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b", "critical"),
    ("api_key", r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{10,}\b", "critical"),
    ("api_key", r"\bAKIA[0-9A-Z]{12,20}\b", "critical"),
    ("database_url", r"\b(?:postgres|postgresql|mysql|mongodb|redis)://[^\s'\"]+", "critical"),
    ("secret", r"\b[A-Z0-9_]*(?:TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY)[A-Z0-9_]*\s*=\s*[^\s'\"]{6,}", "critical"),
]


def scan(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for category, pattern, severity in SECRET_PATTERNS:
        for match in re.finditer(pattern, text, re.I | re.M):
            findings.append(Finding(category, match.start(), match.end(), match.group(0), "secrets", severity))
    return findings
