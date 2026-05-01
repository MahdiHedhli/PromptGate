from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Finding:
    category: str
    start: int
    end: int
    value: str
    detector: str
    severity: str = "medium"
    rule_id: str | None = None
    normalized: bool = False
    safe_replace: bool = True

    def overlaps(self, other: "Finding") -> bool:
        return self.start < other.end and other.start < self.end


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3, "critical": 4}
ACTION_RANK = {"allow": 0, "audit": 1, "mask": 2, "tokenize": 3, "block": 4}


def merge_findings(findings: list[Finding], actions: dict[str, str]) -> list[Finding]:
    ordered = sorted(
        findings,
        key=lambda f: (
            f.start,
            -(f.end - f.start),
            -ACTION_RANK.get(actions.get(f.category, "audit"), 1),
            -SEVERITY_RANK.get(f.severity, 2),
        ),
    )
    kept: list[Finding] = []
    for finding in ordered:
        if not any(finding.overlaps(existing) for existing in kept):
            kept.append(finding)
            continue
        winner = max(
            [finding, *[existing for existing in kept if finding.overlaps(existing)]],
            key=lambda f: (
                ACTION_RANK.get(actions.get(f.category, "audit"), 1),
                SEVERITY_RANK.get(f.severity, 2),
                f.end - f.start,
            ),
        )
        if winner == finding:
            kept = [existing for existing in kept if not finding.overlaps(existing)]
            kept.append(finding)
    return sorted(kept, key=lambda f: f.start)
