from __future__ import annotations

import json
import os
from pathlib import Path

CAPTURE_PATH = Path(os.getenv("PROMPTGATE_MITM_JSONL", "/captures/requests.jsonl"))


def request(flow):
    CAPTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    body = flow.request.get_text(strict=False)
    event = {
        "method": flow.request.method,
        "url": flow.request.pretty_url,
        "headers": {
            key: "[redacted]" if key.lower() in {"authorization", "x-api-key"} else value
            for key, value in flow.request.headers.items()
        },
        "body": body,
    }
    with CAPTURE_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
