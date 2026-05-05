from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator

import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from promptgate.config import current_settings
from promptgate.gateway import process_payload
from promptgate.policy import load_policy
from promptgate.providers import mock
from promptgate.providers.upstream import UpstreamConfigError, forward, forward_stream
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


@app.get("/")
async def root() -> dict:
    return {
        "name": "PromptGate",
        "status": "ok",
        "health": "/health",
        "models": "/v1/models",
        "openai_chat": "/v1/chat/completions",
        "docs": "/docs",
    }


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


def _models_payload() -> dict:
    return {
        "object": "list",
        "data": [
            {
                "id": model,
                "object": "model",
                "created": 0,
                "owned_by": "promptgate-local",
            }
            for model in current_settings().model_list
        ],
    }


@app.get("/v1/models")
async def models() -> dict:
    return _models_payload()


@app.get("/models")
async def models_unversioned() -> dict:
    return _models_payload()


@app.get("/mock/received")
async def mock_received() -> dict:
    return {"received": mock.received()}


@app.post("/mock/reset")
async def mock_reset() -> dict:
    mock.reset()
    return {"ok": True}


@app.post("/v1/chat/completions")
async def chat_completions(payload: dict, authorization: str | None = Header(default=None)):
    return await _chat_completions_impl(payload, authorization)


@app.post("/chat/completions")
async def chat_completions_unversioned(payload: dict, authorization: str | None = Header(default=None)):
    return await _chat_completions_impl(payload, authorization)


async def _chat_completions_impl(payload: dict, authorization: str | None) -> JSONResponse | StreamingResponse:
    _authorize(authorization)
    result = process_payload(payload, _policy(), vault)
    if not result.allowed:
        return JSONResponse(status_code=400, content={"error": {"message": "PromptGate blocked sensitive content", "categories": result.blocked_categories}})
    if payload.get("stream") is True:
        return StreamingResponse(
            _send_upstream_stream("/v1/chat/completions", result.payload),
            media_type="text/event-stream",
            headers={"x-promptgate-findings": str(len(result.audit))},
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
            content={"type": "error", "error": {"message": "PromptGate 0.1.0 rejects Anthropic streaming requests safely; set stream=false or omit stream."}},
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
            return await forward(
                endpoint,
                payload,
                settings.upstream_base_url,
                settings.upstream_api_key,
                settings.upstream_http_proxy,
                settings.upstream_ca_bundle,
            )
        except UpstreamConfigError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=exc.response.status_code, detail="upstream provider returned an error") from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=_safe_upstream_error(exc)) from exc
    raise HTTPException(status_code=503, detail="invalid PROMPTGATE_PROVIDER_MODE")


async def _send_upstream_stream(endpoint: str, payload: dict) -> AsyncIterator[bytes]:
    settings = current_settings()
    if settings.provider_mode == "mock":
        async for chunk in _mock_chat_stream(payload):
            yield chunk
        return
    if settings.provider_mode == "upstream":
        try:
            async for chunk in forward_stream(
                endpoint,
                payload,
                settings.upstream_base_url,
                settings.upstream_api_key,
                settings.upstream_http_proxy,
                settings.upstream_ca_bundle,
            ):
                yield chunk
            return
        except UpstreamConfigError as exc:
            yield _sse_error(str(exc))
            return
        except httpx.HTTPStatusError as exc:
            yield _sse_error(f"upstream provider returned HTTP {exc.response.status_code}")
            yield b"data: [DONE]\n\n"
            return
        except httpx.HTTPError as exc:
            yield _sse_error(_safe_upstream_error(exc))
            yield b"data: [DONE]\n\n"
            return
    yield _sse_error("invalid PROMPTGATE_PROVIDER_MODE")


async def _mock_chat_stream(payload: dict) -> AsyncIterator[bytes]:
    await mock.chat_completion(payload)
    model = payload.get("model", "mock")
    chunk = {
        "id": "promptgate-mock-stream",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "delta": {"content": "mock response"}, "finish_reason": None}],
    }
    done = {
        "id": "promptgate-mock-stream",
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model,
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    }
    yield f"data: {json.dumps(chunk, separators=(',', ':'))}\n\n".encode("utf-8")
    yield f"data: {json.dumps(done, separators=(',', ':'))}\n\n".encode("utf-8")
    yield b"data: [DONE]\n\n"


def _sse_error(message: str) -> bytes:
    payload = {"error": {"message": message}}
    return f"data: {json.dumps(payload, separators=(',', ':'))}\n\n".encode("utf-8")


def _safe_upstream_error(exc: httpx.HTTPError) -> str:
    if isinstance(exc, httpx.ConnectError) and "CERTIFICATE_VERIFY_FAILED" in str(exc):
        return "upstream TLS verification failed; configure PROMPTGATE_UPSTREAM_CA_BUNDLE for the MITM demo"
    return f"upstream request failed: {exc.__class__.__name__}"
