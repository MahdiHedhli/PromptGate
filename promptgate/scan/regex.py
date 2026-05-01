from __future__ import annotations

import re

from promptgate.scan.findings import Finding

PATTERNS: list[tuple[str, str, str, str]] = [
    ("private_email", r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "regex", "high"),
    ("private_phone", r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)", "regex", "medium"),
    ("ip_address", r"\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b", "regex", "medium"),
    ("ip_address", r"\b(?:[A-F0-9]{1,4}:){2,7}[A-F0-9]{1,4}\b", "regex", "medium"),
    ("private_url", r"\bhttps?://[^\s<>'\"]+", "regex", "medium"),
    ("internal_domain", r"\b(?:[a-z0-9-]+\.)+(?:corp|internal|local|lan|example)\b", "regex", "medium"),
    ("file_path", r"(?:/Users|/home|/var|/etc|/opt|/srv)/[^\s'\"]+", "regex", "medium"),
]

DOMAIN_RE = re.compile(r"\b(?!(?:https?://))([a-z0-9-]+\.)+[a-z]{2,}\b", re.I)


def scan(text: str, custom_rules: list[dict] | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for category, pattern, detector, severity in PATTERNS:
        for match in re.finditer(pattern, text, re.I | re.M):
            findings.append(Finding(category, match.start(), match.end(), match.group(0), detector, severity))
    for match in DOMAIN_RE.finditer(text):
        value = match.group(0)
        if "@" not in value and not value.endswith((".md", ".py", ".txt", ".yaml")):
            findings.append(Finding("private_url", match.start(), match.end(), value, "regex", "low"))
    for rule in custom_rules or []:
        if rule.get("type") == "regex":
            for match in re.finditer(rule["pattern"], text, re.I | re.M):
                findings.append(
                    Finding(
                        rule.get("category", rule["id"]),
                        match.start(),
                        match.end(),
                        match.group(0),
                        "custom_regex",
                        rule.get("severity", "medium"),
                        rule.get("id"),
                    )
                )
        if rule.get("type") == "keyword":
            for value in rule.get("values", []):
                for match in re.finditer(re.escape(value), text, re.I):
                    findings.append(
                        Finding(
                            rule.get("category", rule["id"]),
                            match.start(),
                            match.end(),
                            match.group(0),
                            "keyword",
                            rule.get("severity", "medium"),
                            rule.get("id"),
                        )
                    )
    return findings
