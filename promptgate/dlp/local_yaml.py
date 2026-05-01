from __future__ import annotations

from pathlib import Path

from promptgate.policy import Policy, load_policy


class LocalYamlAdapter:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_policy(self) -> Policy:
        return load_policy(self.path)

    def load_rules(self) -> list[dict]:
        return self.load_policy().rules
