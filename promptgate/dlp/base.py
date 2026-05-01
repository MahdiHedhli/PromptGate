from __future__ import annotations

from typing import Protocol


class DLPAdapter(Protocol):
    def load_rules(self) -> list[dict]:
        ...
