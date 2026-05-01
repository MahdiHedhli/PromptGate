from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

from promptgate.extract import extract_texts, rewrite_text_value, set_path
from promptgate.policy import Policy
from promptgate.redact import TokenVault, apply_actions
from promptgate.scan import normalize, privacy_filter, regex, secrets

logger = logging.getLogger("promptgate")


@dataclass
class GatewayResult:
    allowed: bool
    payload: dict
    audit: list[dict]
    blocked_categories: list[str]
    latency_ms: float
    timings: dict[str, float]
    streaming_rejected: bool = False


def process_payload(payload: dict, policy: Policy, vault: TokenVault | None = None) -> GatewayResult:
    started = time.perf_counter()
    vault = vault or TokenVault()
    updated = payload
    audit: list[dict] = []
    blocked: list[str] = []
    timings = {"extract_ms": 0.0, "scan_ms": 0.0, "decision_rewrite_ms": 0.0, "total_ms": 0.0}
    extract_started = time.perf_counter()
    text_items = extract_texts(payload)
    conversation_id = _conversation_id(payload)
    timings["extract_ms"] = (time.perf_counter() - extract_started) * 1000
    for item in text_items:
        scan_started = time.perf_counter()
        findings = []
        if policy.detectors.regex:
            findings.extend(regex.scan(item.text, policy.rules))
        if policy.detectors.secrets:
            findings.extend(secrets.scan(item.text))
        provider = _privacy_filter_provider(policy.detectors.privacy_filter)
        if provider is not None:
            findings.extend(privacy_filter.scan(item.text, provider))
        if policy.detectors.normalization:
            findings.extend(normalize.scan(item.text))
        timings["scan_ms"] += (time.perf_counter() - scan_started) * 1000
        decision_started = time.perf_counter()
        result = apply_actions(item.text, findings, policy, vault, conversation_id=conversation_id)
        audit.extend(result.actions)
        blocked.extend(result.blocked_categories)
        if not result.allowed:
            timings["decision_rewrite_ms"] += (time.perf_counter() - decision_started) * 1000
            continue
        updated = set_path(updated, item.path, rewrite_text_value(item.text, result.text, item.json_encoded))
        timings["decision_rewrite_ms"] += (time.perf_counter() - decision_started) * 1000
    latency = (time.perf_counter() - started) * 1000
    timings["total_ms"] = latency
    timings = {key: round(value, 3) for key, value in timings.items()}
    event = {"findings": len(audit), "blocked_categories": sorted(set(blocked)), "latency_ms": round(latency, 2)}
    logger.info("promptgate_audit %s", event)
    return GatewayResult(not blocked or policy.mode != "enforce", updated, audit, sorted(set(blocked)), latency, timings)


def _privacy_filter_provider(config: str | bool | dict | None) -> privacy_filter.PrivacyFilterProvider | None:
    if config in {True, "enabled"}:
        return privacy_filter.MockPrivacyFilterProvider()
    if not isinstance(config, dict) or not config.get("enabled", False):
        return None
    if config.get("mode") == "local_service":
        return privacy_filter.LocalServicePrivacyFilterProvider(str(config["url"]), float(config.get("timeout_seconds", 2.0)))
    return privacy_filter.MockPrivacyFilterProvider()


def _conversation_id(payload: dict) -> str:
    for key in ("conversation_id", "thread_id", "session_id", "request_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        for key in ("conversation_id", "thread_id", "session_id", "request_id"):
            value = metadata.get(key)
            if isinstance(value, str) and value:
                return value
    return f"request:{uuid.uuid4().hex}"
