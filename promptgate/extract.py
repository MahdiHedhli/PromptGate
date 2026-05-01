from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


@dataclass
class TextPath:
    path: tuple[Any, ...]
    text: str
    json_encoded: bool = False


TEXT_KEYS = {
    "content",
    "text",
    "input",
    "output",
    "result",
    "results",
    "system",
    "developer",
    "instructions",
    "prompt",
    "completion",
    "arguments",
    "metadata",
    "summary",
    "description",
}
JSON_STRING_KEYS = {"arguments", "input", "metadata", "content", "output", "result"}
TEXT_CONTEXT_KEYS = {"metadata", "tool_result", "tool_results", "mcp", "annotations"}


def extract_texts(payload: Any) -> list[TextPath]:
    results: list[TextPath] = []

    def walk(value: Any, path: tuple[Any, ...], text_context: bool = False) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_context = text_context or key in TEXT_CONTEXT_KEYS
                if isinstance(child, str) and (key in TEXT_KEYS or child_context):
                    json_text = _extract_json_string(child)
                    if json_text is not None and key in JSON_STRING_KEYS:
                        results.append(TextPath((*path, key), child, json_encoded=True))
                    else:
                        results.append(TextPath((*path, key), child))
                else:
                    walk(child, (*path, key), child_context)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, (*path, index), text_context)

    walk(payload, ())
    return results


def _extract_json_string(text: str) -> Any | None:
    stripped = text.strip()
    if not stripped or stripped[0] not in "[{":
        return None
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        return None


def rewrite_text_value(original: str, rewritten_text: str, json_encoded: bool) -> str:
    if not json_encoded:
        return rewritten_text
    rewritten_parsed = _extract_json_string(rewritten_text)
    if rewritten_parsed is not None:
        return json.dumps(rewritten_parsed, separators=(",", ":"), ensure_ascii=False)
    parsed = _extract_json_string(original)
    if parsed is None:
        return rewritten_text
    replacement = _rewrite_json_strings(parsed, original, rewritten_text)
    return json.dumps(replacement, separators=(",", ":"), ensure_ascii=False)


def _rewrite_json_strings(value: Any, original: str, rewritten_text: str) -> Any:
    if isinstance(value, str):
        return rewritten_text if value == original else value
    if isinstance(value, dict):
        return {key: _rewrite_json_strings(child, original, rewritten_text) for key, child in value.items()}
    if isinstance(value, list):
        return [_rewrite_json_strings(child, original, rewritten_text) for child in value]
    return value


def set_path(payload: dict, path: tuple[Any, ...], value: str) -> dict:
    updated = deepcopy(payload)
    cursor: Any = updated
    for key in path[:-1]:
        cursor = cursor[key]
    cursor[path[-1]] = value
    return updated
