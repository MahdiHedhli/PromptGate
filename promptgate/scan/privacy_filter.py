from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from promptgate.scan.findings import Finding

LABEL_MAP = {
    "private_person": "private_person",
    "private_address": "private_address",
    "private_email": "private_email",
    "private_phone": "private_phone",
    "private_url": "private_url",
    "private_date": "private_date",
    "account_number": "account_number",
    "secret": "secret",
}


@dataclass(frozen=True)
class PrivacyFilterHit:
    label: str
    start: int
    end: int
    score: float = 1.0


class PrivacyFilterProvider(Protocol):
    def find(self, text: str) -> list[PrivacyFilterHit]:
        ...


class MockPrivacyFilterProvider:
    def __init__(self, hits: list[PrivacyFilterHit] | None = None) -> None:
        self.hits = hits or []

    def find(self, text: str) -> list[PrivacyFilterHit]:
        return self.hits


def scan(text: str, provider: PrivacyFilterProvider | None = None) -> list[Finding]:
    if provider is None:
        return []
    findings: list[Finding] = []
    for hit in provider.find(text):
        category = LABEL_MAP.get(hit.label)
        if not category:
            continue
        findings.append(Finding(category, hit.start, hit.end, text[hit.start:hit.end], "privacy_filter", "high"))
    return findings
