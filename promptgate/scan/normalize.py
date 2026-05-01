from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from promptgate.scan.findings import Finding

ZERO_WIDTH_RE = re.compile("[\u200b\u200c\u200d\ufeff]")
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t"})
CONFUSABLES = str.maketrans({"＠": "@", "．": ".", "。": ".", "а": "a", "е": "e", "о": "o"})


@dataclass(frozen=True)
class MappedText:
    text: str
    spans: list[tuple[int, int]]


def normalize_for_detection(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).translate(CONFUSABLES)
    value = ZERO_WIDTH_RE.sub("", value)
    value = re.sub(r"\b(at)\b", "@", value, flags=re.I)
    value = re.sub(r"\b(dot)\b", ".", value, flags=re.I)
    value = re.sub(r"\s*@\s*", "@", value)
    value = re.sub(r"\s*\.\s*", ".", value)
    value = re.sub(r"\b([A-Za-z0-9])(?:[\s-]+)(?=[A-Za-z0-9]\b)", r"\1", value)
    value = re.sub(r"\bsk[\s-]+([a-z0-9][a-z0-9\s_-]{8,})", lambda m: "sk-" + re.sub(r"[\s_-]+", "", m.group(1)), value, flags=re.I)
    value = re.sub(r"\bAKIA(?:[\s-]+[A-Z0-9]+){3,}", lambda m: re.sub(r"[\s-]+", "", m.group(0)), value, flags=re.I)
    return value.translate(LEET)


def normalize_with_mapping(text: str) -> MappedText:
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    for index, original in enumerate(text):
        normalized = unicodedata.normalize("NFKC", original).translate(CONFUSABLES)
        if ZERO_WIDTH_RE.fullmatch(normalized):
            continue
        normalized = normalized.translate(LEET)
        for char in normalized:
            chars.append(char)
            spans.append((index, index + 1))
    mapped = MappedText("".join(chars), spans)
    mapped = _replace_words(mapped, {"at": "@", "dot": "."})
    mapped = _collapse_email_separators(mapped)
    mapped = _collapse_split_secret_prefix(mapped)
    return mapped


def _replace_words(mapped: MappedText, replacements: dict[str, str]) -> MappedText:
    tokens: list[str] = []
    spans: list[tuple[int, int]] = []
    index = 0
    pattern = re.compile(r"\b(?:" + "|".join(re.escape(k) for k in replacements) + r")\b", re.I)
    for match in pattern.finditer(mapped.text):
        tokens.extend(mapped.text[index:match.start()])
        spans.extend(mapped.spans[index:match.start()])
        replacement = replacements[match.group(0).lower()]
        tokens.append(replacement)
        original_spans = mapped.spans[match.start() : match.end()]
        spans.append((original_spans[0][0], original_spans[-1][1]))
        index = match.end()
    tokens.extend(mapped.text[index:])
    spans.extend(mapped.spans[index:])
    return MappedText("".join(tokens), spans)


def _collapse_email_separators(mapped: MappedText) -> MappedText:
    text = mapped.text
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    for index, char in enumerate(text):
        if char in {" ", "\t", "\n", "-", "_"}:
            prev_char = _previous_non_space(text, index)
            next_char = _next_non_space(text, index)
            if prev_char and next_char and (prev_char.isalnum() or prev_char in ".@") and (next_char.isalnum() or next_char in ".@"):
                continue
        chars.append(char)
        spans.append(mapped.spans[index])
    return MappedText("".join(chars), spans)


def _collapse_split_secret_prefix(mapped: MappedText) -> MappedText:
    pattern = re.compile(r"\bsk[\s-]+([a-z0-9][a-z0-9\s_-]{8,})", re.I)
    text = mapped.text
    chars: list[str] = []
    spans: list[tuple[int, int]] = []
    cursor = 0
    for match in pattern.finditer(text):
        chars.extend(text[cursor:match.start()])
        spans.extend(mapped.spans[cursor:match.start()])
        collapsed = re.sub(r"[\s_-]+", "", match.group(1))
        secret = "sk-" + collapsed
        original_spans = mapped.spans[match.start() : match.end()]
        for char in secret:
            chars.append(char)
            spans.append((original_spans[0][0], original_spans[-1][1]))
        cursor = match.end()
    chars.extend(text[cursor:])
    spans.extend(mapped.spans[cursor:])
    return MappedText("".join(chars), spans)


def _previous_non_space(text: str, index: int) -> str | None:
    for char in reversed(text[:index]):
        if not char.isspace():
            return char
    return None


def _next_non_space(text: str, index: int) -> str | None:
    for char in text[index + 1 :]:
        if not char.isspace():
            return char
    return None


def scan(text: str) -> list[Finding]:
    findings: list[Finding] = []
    mapped = normalize_with_mapping(text)
    normalized = mapped.text
    if normalized == text:
        return findings
    from promptgate.scan.regex import scan as regex_scan
    from promptgate.scan.secrets import scan as secret_scan

    mapped_findings = regex_scan(normalized) + secret_scan(normalized)
    for finding in mapped_findings:
        lower = text.lower()
        if finding.category == "private_url" and not any(marker in lower for marker in (" dot ", "http", "\u200b")):
            continue
        if finding.category == "private_email" and not any(marker in lower for marker in (" at ", " dot ", "\u200b")) and "@" in text:
            continue
        if finding.category == "private_email" and normalized.count("@") > 1:
            pass
        elif _mapping_is_reliable(finding, mapped):
            start = min(span[0] for span in mapped.spans[finding.start : finding.end])
            end = max(span[1] for span in mapped.spans[finding.start : finding.end])
            findings.append(
                Finding(
                    finding.category,
                    start,
                    end,
                    text[start:end],
                    "normalization",
                    "high" if finding.severity != "critical" else "critical",
                    normalized=True,
                    safe_replace=True,
                )
            )
            continue
        findings.append(
            Finding(
                finding.category,
                0,
                len(text),
                text,
                "normalization",
                "high" if finding.severity != "critical" else "critical",
                normalized=True,
                safe_replace=False,
            )
        )
    if ZERO_WIDTH_RE.search(text) and not mapped_findings:
        findings.append(Finding("obfuscated_text", 0, len(text), text, "normalization", "high", safe_replace=False))
    return findings


def _mapping_is_reliable(finding: Finding, mapped: MappedText) -> bool:
    relevant = mapped.spans[finding.start : finding.end]
    if not relevant:
        return False
    start = min(span[0] for span in relevant)
    end = max(span[1] for span in relevant)
    return start < end and end - start <= max(256, (finding.end - finding.start) * 4)
