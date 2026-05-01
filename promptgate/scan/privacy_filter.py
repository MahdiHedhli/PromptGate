from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import httpx

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


class PrivacyFilterUnavailable(RuntimeError):
    pass


class LocalServicePrivacyFilterProvider:
    def __init__(self, url: str, timeout_seconds: float = 2.0) -> None:
        self.url = url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def find(self, text: str) -> list[PrivacyFilterHit]:
        try:
            response = httpx.post(f"{self.url}/scan", json={"text": text}, timeout=self.timeout_seconds)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise PrivacyFilterUnavailable(f"Privacy Filter local service is unavailable at {self.url}") from exc
        payload = response.json()
        hits = payload.get("findings", payload if isinstance(payload, list) else [])
        return [
            PrivacyFilterHit(
                label=str(hit["label"]),
                start=int(hit["start"]),
                end=int(hit["end"]),
                score=float(hit.get("score", 1.0)),
            )
            for hit in hits
            if isinstance(hit, dict) and {"label", "start", "end"} <= set(hit)
        ]


def scan(text: str, provider: PrivacyFilterProvider | None = None) -> list[Finding]:
    if provider is None:
        return []
    findings: list[Finding] = []
    for hit in provider.find(text):
        category = LABEL_MAP.get(hit.label)
        if not category:
            continue
        findings.append(Finding(category, hit.start, hit.end, text[hit.start:hit.end], "privacy_filter", "high", confidence=hit.score))
    return findings
