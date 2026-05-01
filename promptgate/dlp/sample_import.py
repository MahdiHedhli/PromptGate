from __future__ import annotations

from pathlib import Path

import yaml


class SampleImportAdapter:
    def __init__(self, sample_dir: str | Path = "policies/samples") -> None:
        self.sample_dir = Path(sample_dir)

    def load_rules(self) -> list[dict]:
        rules: list[dict] = []
        for path in sorted(self.sample_dir.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for rule in data.get("rules", []):
                rules.append(rule)
            for keyword in data.get("keywords", []):
                rules.append(
                    {
                        "id": f"sample_keyword_{keyword.lower().replace(' ', '_')}",
                        "type": "keyword",
                        "values": [keyword],
                        "category": "sample_keyword",
                        "action": "tokenize",
                        "severity": "medium",
                    }
                )
            for rule in data.get("custom_regex", []):
                rules.append({**rule, "type": "regex"})
        return rules
