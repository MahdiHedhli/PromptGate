#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="PromptGate Fake Upstream")
capture_path = Path(os.getenv("PROMPTGATE_FAKE_CAPTURE", "docs/reports/generated/fake-upstream-capture.json"))


async def _capture(request: Request, payload: dict[str, Any]) -> None:
    capture_path.parent.mkdir(parents=True, exist_ok=True)
    headers = {key: "[redacted]" for key in request.headers if key.lower() in {"authorization", "x-api-key"}}
    event = {"path": request.url.path, "headers": headers, "payload": payload}
    existing = []
    if capture_path.exists():
        existing = json.loads(capture_path.read_text(encoding="utf-8"))
    existing.append(event)
    capture_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


@app.post("/v1/chat/completions")
async def chat(payload: dict, request: Request) -> JSONResponse:
    await _capture(request, payload)
    return JSONResponse({"id": "fake-upstream-chat", "choices": [{"message": {"role": "assistant", "content": "fake upstream response"}}]})


@app.post("/v1/messages")
async def messages(payload: dict, request: Request) -> JSONResponse:
    await _capture(request, payload)
    return JSONResponse({"id": "fake-upstream-message", "type": "message", "content": [{"type": "text", "text": "fake upstream response"}]})
