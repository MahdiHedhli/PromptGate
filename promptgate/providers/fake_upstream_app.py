from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="PromptGate Fake Provider")


@app.post("/v1/chat/completions")
async def chat(payload: dict, request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "id": "fake-provider-chat",
            "received_path": request.url.path,
            "choices": [{"message": {"role": "assistant", "content": "fake provider response"}}],
        }
    )


@app.post("/v1/messages")
async def messages(payload: dict, request: Request) -> JSONResponse:
    return JSONResponse(
        {
            "id": "fake-provider-message",
            "type": "message",
            "received_path": request.url.path,
            "content": [{"type": "text", "text": "fake provider response"}],
        }
    )
