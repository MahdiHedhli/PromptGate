from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import hashlib
import json
import yaml
import re


DEFAULT_ACTIONS = {
    "private_email": "tokenize",
    "private_phone": "mask",
    "private_person": "tokenize",
    "private_address": "mask",
    "private_url": "tokenize",
    "private_date": "mask",
    "account_number": "block",
    "secret": "block",
    "jwt": "block",
    "api_key": "block",
    "database_url": "block",
    "internal_domain": "tokenize",
    "ip_address": "tokenize",
    "file_path": "mask",
    "obfuscated_text": "block",
}

VALID_ACTIONS = {"block", "mask", "tokenize", "allow", "audit"}
VALID_SEVERITIES = {"low", "medium", "high", "critical"}
VALID_MODES = {"enforce", "audit", "dry-run"}
VALID_PROFILES = {"software_saas", "security_consulting", "finance", "healthcare", "legal", "media_entertainment"}
VALID_DETECTORS = {"regex", "secrets", "privacy_filter", "normalization", "sample_dlp_imports"}
VALID_PRIVACY_FILTER_VALUES = {True, False, "optional", "enabled", "disabled"}
VALID_RULE_TYPES = {"regex", "keyword"}
REQUIRED_SECTIONS = {"profile", "mode", "logging", "detectors", "actions", "rules"}
VALID_TOKENIZATION_MODES = {"scoped_random", "deterministic"}


class PolicyValidationError(ValueError):
    def __init__(self, path: str | Path | None, message: str, rule_id: str | None = None) -> None:
        prefix = f"{path}: " if path else ""
        suffix = f" (rule_id={rule_id})" if rule_id else ""
        super().__init__(f"{prefix}{message}{suffix}")
        self.path = str(path) if path else None
        self.rule_id = rule_id


@dataclass
class LoggingPolicy:
    raw_prompts: bool = False
    redacted_prompts: bool = True
    findings: bool = True


@dataclass
class DetectorPolicy:
    regex: bool = True
    secrets: bool = True
    privacy_filter: str | bool | dict[str, Any] = False
    normalization: bool = True
    sample_dlp_imports: bool = True


@dataclass
class TokenizationPolicy:
    mode: str = "scoped_random"
    ttl_seconds: int = 3600
    max_conversations: int = 100
    restore_responses: bool = False


@dataclass
class Policy:
    profile: str = "security_consulting"
    mode: str = "enforce"
    audit_only: bool = False
    logging: LoggingPolicy = field(default_factory=LoggingPolicy)
    detectors: DetectorPolicy = field(default_factory=DetectorPolicy)
    tokenization: TokenizationPolicy = field(default_factory=TokenizationPolicy)
    actions: dict[str, str] = field(default_factory=lambda: DEFAULT_ACTIONS.copy())
    rules: list[dict[str, Any]] = field(default_factory=list)
    allowlist: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any], path: str | Path | None = None) -> "Policy":
        validate_policy_data(data, path)
        policy = cls()
        policy.profile = data.get("profile", policy.profile)
        policy.mode = data.get("mode", policy.mode)
        policy.audit_only = bool(data.get("audit_only", policy.audit_only))
        policy.logging = LoggingPolicy(**{**policy.logging.__dict__, **data.get("logging", {})})
        policy.detectors = DetectorPolicy(**{**policy.detectors.__dict__, **data.get("detectors", {})})
        policy.tokenization = TokenizationPolicy(**{**policy.tokenization.__dict__, **data.get("tokenization", {})})
        policy.actions.update(data.get("actions", {}))
        policy.rules = data.get("rules", [])
        policy.allowlist = data.get("allowlist", [])
        for rule in policy.rules:
            if "action" in rule:
                policy.actions[rule.get("category", rule["id"])] = rule["action"]
        return policy

    def action_for(self, category: str) -> str:
        return self.actions.get(category, "audit")

    def is_audit_only(self, rule_id: str | None = None) -> bool:
        if self.mode in {"audit", "dry-run"} or self.audit_only:
            return True
        if rule_id:
            for rule in self.rules:
                if rule.get("id") == rule_id and "audit_only" in rule:
                    return bool(rule["audit_only"])
        return False

    def policy_hash(self) -> str:
        data = {
            "profile": self.profile,
            "mode": self.mode,
            "audit_only": self.audit_only,
            "detectors": self.detectors.__dict__,
            "tokenization": self.tokenization.__dict__,
            "actions": self.actions,
            "rules": self.rules,
            "allowlist": self.allowlist,
        }
        encoded = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]


def load_policy(path: str | Path) -> Policy:
    with Path(path).open("r", encoding="utf-8") as handle:
        return Policy.from_dict(yaml.safe_load(handle) or {}, Path(path))


def dump_policy(policy: Policy, path: str | Path) -> None:
    data = {
        "profile": policy.profile,
        "mode": policy.mode,
        "audit_only": policy.audit_only,
        "logging": policy.logging.__dict__,
        "detectors": policy.detectors.__dict__,
        "tokenization": policy.tokenization.__dict__,
        "actions": policy.actions,
        "allowlist": policy.allowlist,
        "rules": policy.rules,
    }
    Path(path).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def validate_policy_data(data: dict[str, Any], path: str | Path | None = None) -> None:
    if not isinstance(data, dict):
        raise PolicyValidationError(path, "policy must be a YAML mapping")
    missing = sorted(REQUIRED_SECTIONS - set(data))
    if missing:
        raise PolicyValidationError(path, f"missing required section(s): {', '.join(missing)}")
    if data.get("profile") not in VALID_PROFILES:
        raise PolicyValidationError(path, f"invalid industry profile '{data.get('profile')}'")
    if data.get("mode") not in VALID_MODES:
        raise PolicyValidationError(path, f"invalid policy mode '{data.get('mode')}'")
    if "audit_only" in data and not isinstance(data["audit_only"], bool):
        raise PolicyValidationError(path, "audit_only must be true or false")
    _validate_mapping(path, "logging", data.get("logging"), {"raw_prompts", "redacted_prompts", "findings"})
    detectors = _validate_mapping(path, "detectors", data.get("detectors"), VALID_DETECTORS)
    for detector, enabled in detectors.items():
        if detector == "privacy_filter":
            if isinstance(enabled, dict):
                _validate_privacy_filter_config(path, enabled)
            elif enabled not in VALID_PRIVACY_FILTER_VALUES:
                raise PolicyValidationError(path, f"invalid privacy_filter value '{enabled}'")
        elif not isinstance(enabled, bool):
            raise PolicyValidationError(path, f"detector '{detector}' must be true or false")
    actions = _validate_mapping(path, "actions", data.get("actions"), None)
    for category, action in actions.items():
        if action not in VALID_ACTIONS:
            raise PolicyValidationError(path, f"unknown action '{action}' for category '{category}'")
    tokenization = data.get("tokenization", {})
    if tokenization is not None:
        tokenization = _validate_mapping(path, "tokenization", tokenization, {"mode", "ttl_seconds", "max_conversations", "restore_responses"})
        if tokenization.get("mode", "scoped_random") not in VALID_TOKENIZATION_MODES:
            raise PolicyValidationError(path, f"invalid tokenization mode '{tokenization.get('mode')}'")
        for key in ("ttl_seconds", "max_conversations"):
            if key in tokenization and (not isinstance(tokenization[key], int) or tokenization[key] <= 0):
                raise PolicyValidationError(path, f"tokenization.{key} must be a positive integer")
        if "restore_responses" in tokenization and not isinstance(tokenization["restore_responses"], bool):
            raise PolicyValidationError(path, "tokenization.restore_responses must be true or false")
    allowlist = data.get("allowlist", [])
    if allowlist is not None and not isinstance(allowlist, list):
        raise PolicyValidationError(path, "allowlist must be a list")
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise PolicyValidationError(path, "rules must be a list")
    seen: set[str] = set()
    for index, rule in enumerate(rules):
        _validate_rule(path, rule, index, seen)


def _validate_mapping(path: str | Path | None, name: str, value: Any, allowed_keys: set[str] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PolicyValidationError(path, f"{name} must be a mapping")
    if allowed_keys is not None:
        unknown = sorted(set(value) - allowed_keys)
        if unknown:
            raise PolicyValidationError(path, f"unknown {name} key(s): {', '.join(unknown)}")
    return value


def _validate_privacy_filter_config(path: str | Path | None, value: dict[str, Any]) -> None:
    unknown = sorted(set(value) - {"enabled", "mode", "url", "timeout_seconds", "fail_closed"})
    if unknown:
        raise PolicyValidationError(path, f"unknown privacy_filter key(s): {', '.join(unknown)}")
    if not isinstance(value.get("enabled", False), bool):
        raise PolicyValidationError(path, "privacy_filter.enabled must be true or false")
    if value.get("mode", "mock") not in {"mock", "local_service"}:
        raise PolicyValidationError(path, f"invalid privacy_filter mode '{value.get('mode')}'")
    if value.get("mode") == "local_service" and not isinstance(value.get("url"), str):
        raise PolicyValidationError(path, "privacy_filter local_service mode requires url")
    if "timeout_seconds" in value and not isinstance(value["timeout_seconds"], int | float):
        raise PolicyValidationError(path, "privacy_filter.timeout_seconds must be numeric")
    if "fail_closed" in value and not isinstance(value["fail_closed"], bool):
        raise PolicyValidationError(path, "privacy_filter.fail_closed must be true or false")


def _validate_rule(path: str | Path | None, rule: Any, index: int, seen: set[str]) -> None:
    if not isinstance(rule, dict):
        raise PolicyValidationError(path, f"rule at index {index} must be a mapping")
    rule_id = rule.get("id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        raise PolicyValidationError(path, f"rule at index {index} must have a non-empty id")
    if rule_id in seen:
        raise PolicyValidationError(path, "duplicate rule id", rule_id)
    seen.add(rule_id)
    if not re.fullmatch(r"[A-Za-z0-9_.:-]+", rule_id):
        raise PolicyValidationError(path, "rule id contains unsupported characters", rule_id)
    rule_type = rule.get("type")
    if rule_type not in VALID_RULE_TYPES:
        raise PolicyValidationError(path, f"invalid rule type '{rule_type}'", rule_id)
    action = rule.get("action")
    if action is not None and action not in VALID_ACTIONS:
        raise PolicyValidationError(path, f"unknown rule action '{action}'", rule_id)
    severity = rule.get("severity", "medium")
    if severity not in VALID_SEVERITIES:
        raise PolicyValidationError(path, f"invalid severity '{severity}'", rule_id)
    if "audit_only" in rule and not isinstance(rule["audit_only"], bool):
        raise PolicyValidationError(path, "rule audit_only must be true or false", rule_id)
    if "category" in rule and not isinstance(rule["category"], str):
        raise PolicyValidationError(path, "rule category must be a string", rule_id)
    if rule_type == "regex":
        pattern = rule.get("pattern")
        if not isinstance(pattern, str) or not pattern:
            raise PolicyValidationError(path, "regex rule requires a pattern", rule_id)
        try:
            re.compile(pattern)
        except re.error as exc:
            raise PolicyValidationError(path, f"invalid regex pattern: {exc}", rule_id) from exc
    if rule_type == "keyword":
        values = rule.get("values")
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value for value in values):
            raise PolicyValidationError(path, "keyword rule requires non-empty string values", rule_id)
