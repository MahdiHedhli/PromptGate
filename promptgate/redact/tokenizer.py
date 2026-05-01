from __future__ import annotations

from collections import defaultdict


class TokenVault:
    def __init__(self) -> None:
        self._tokens: dict[tuple[str, str], str] = {}
        self._counts: defaultdict[str, int] = defaultdict(int)

    def token_for(self, category: str, raw: str, prefix: str | None = None) -> str:
        key = (category, raw)
        if key in self._tokens:
            return self._tokens[key]
        self._counts[category] += 1
        label = (prefix or category).upper()
        token = f"[{label}_{self._counts[category]:03d}]"
        self._tokens[key] = token
        return token
