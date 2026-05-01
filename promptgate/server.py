from __future__ import annotations

import logging

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from promptgate.config import current_settings
from promptgate.gateway import process_payload
from promptgate.policy import load_policy
from promptgate.providers import mock
from promptgate.providers.upstream import UpstreamConfigError, forward
from promptgate.redact import TokenVault

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI(title="PromptGate", version="0.1.0")
vault = TokenVault()


def _policy():
    return load_policy(current_settings().policy_path)


def _authorize(auth: str | None) -> None:
    settings = current_settings()
    if settings.unsafe_dev_no_auth:
        return
    if not settings.local_auth_token:
        raise HTTPException(status_code=503, detail="PromptGate local auth token is not configured")
    if auth is None:
        raise HTTPException(status_code=401, detail="missing local PromptGate token")
    if auth.startswith("Bearer ") and auth.removeprefix("Bearer ") == settings.local_auth_token:
        return
    raise HTTPException(status_code=401, detail="invalid local PromptGate token")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/status")
async def status() -> dict:
    policy = _policy()
    return {
        "profile": policy.profile,
        "mode": policy.mode,
        "detectors": policy.detectors.__dict__,
        "raw_prompt_logging": policy.logging.raw_prompts,
        "provider_mode": current_settings().provider_mode,
        "auth_required": not current_settings().unsafe_dev_no_auth,
    }


@app.get("/mock/received")
async def mock_received() -> dict:
    return {"received": mock.received()}


@app.post("/mock/reset")
async def mock_reset() -> dict:
    mock.reset()
    return {"ok": True}


@app.post("/v1/chat/completions")
async def chat_completions(payload: dict, authorization: str | None = Header(default=None)) -> JSONResponse:
    _authorize(authorization)
    result = process_payload(payload, _policy(), vault)
    if not result.allowed:
        return JSONResponse(status_code=400, content={"error": {"message": "PromptGate blocked sensitive content", "categories": result.blocked_categories}})
    if payload.get("stream") is True:
        return JSONResponse(
            status_code=400,
            content={"error": {"message": "PromptGate 0.1.0 rejects streaming requests safely; set stream=false or omit stream."}},
        )
    response = await _send_upstream("/v1/chat/completions", result.payload, "chat")
    return JSONResponse(content=response, headers={"x-promptgate-findings": str(len(result.audit))})


@app.post("/v1/messages")
async def anthropic_messages(payload: dict, x_api_key: str | None = Header(default=None), authorization: str | None = Header(default=None)) -> JSONResponse:
    _authorize(authorization or (f"Bearer {x_api_key}" if x_api_key else None))
    result = process_payload(payload, _policy(), vault)
    if not result.allowed:
        return JSONResponse(status_code=400, content={"type": "error", "error": {"message": "PromptGate blocked sensitive content", "categories": result.blocked_categories}})
    if payload.get("stream") is True:
        return JSONResponse(
            status_code=400,
            content={"type": "error", "error": {"message": "PromptGate 0.1.0 rejects streaming requests safely; set stream=false or omit stream."}},
        )
    response = await _send_upstream("/v1/messages", result.payload, "anthropic")
    return JSONResponse(content=response, headers={"x-promptgate-findings": str(len(result.audit))})


async def _send_upstream(endpoint: str, payload: dict, mock_kind: str) -> dict:
    settings = current_settings()
    if settings.provider_mode == "mock":
        if mock_kind == "anthropic":
            return await mock.anthropic_message(payload)
        return await mock.chat_completion(payload)
    if settings.provider_mode == "upstream":
        try:
            return await forward(endpoint, payload, settings.upstream_base_url, settings.upstream_api_key)
        except UpstreamConfigError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    raise HTTPException(status_code=503, detail="invalid PROMPTGATE_PROVIDER_MODE")
