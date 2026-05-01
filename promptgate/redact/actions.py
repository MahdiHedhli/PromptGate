from __future__ import annotations

from dataclasses import dataclass

from promptgate.policy import Policy
from promptgate.redact.tokenizer import TokenVault
from promptgate.scan.findings import Finding, merge_findings


@dataclass
class RedactionResult:
    allowed: bool
    text: str
    findings: list[Finding]
    actions: list[dict]
    blocked_categories: list[str]


def apply_actions(text: str, findings: list[Finding], policy: Policy, vault: TokenVault) -> RedactionResult:
    findings = [f for f in findings if not any(allowed in f.value for allowed in policy.allowlist)]
    actions_by_category = {category: policy.action_for(category) for category in policy.actions}
    merged = merge_findings(findings, actions_by_category)
    blocked = [f.category for f in merged if policy.action_for(f.category) == "block" or not f.safe_replace]
    action_log: list[dict] = []
    if blocked and policy.mode == "enforce":
        for finding in merged:
            action_log.append(_metadata(finding, policy.action_for(finding.category)))
        return RedactionResult(False, text, merged, action_log, sorted(set(blocked)))

    pieces: list[str] = []
    cursor = 0
    for finding in merged:
        action = policy.action_for(finding.category)
        pieces.append(text[cursor:finding.start])
        if action == "mask":
            pieces.append(f"[{finding.category.upper()}_REDACTED]")
        elif action == "tokenize":
            prefix = _rule_prefix(policy, finding)
            pieces.append(vault.token_for(finding.category, text[finding.start:finding.end], prefix))
        else:
            pieces.append(text[finding.start:finding.end])
        cursor = finding.end
        action_log.append(_metadata(finding, action))
    pieces.append(text[cursor:])
    return RedactionResult(True, "".join(pieces), merged, action_log, [])


def _rule_prefix(policy: Policy, finding: Finding) -> str | None:
    for rule in policy.rules:
        if rule.get("id") == finding.rule_id:
            return rule.get("token_prefix")
    return None


def _metadata(finding: Finding, action: str) -> dict:
    metadata = {
        "category": finding.category,
        "severity": finding.severity,
        "detector": finding.detector,
        "action": action,
        "rule_id": finding.rule_id,
        "normalized": finding.normalized,
    }
    if not finding.safe_replace:
        metadata["reason"] = "normalized finding could not be safely mapped to an original span"
    return metadata
