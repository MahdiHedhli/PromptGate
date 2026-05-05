from fastapi.testclient import TestClient
import httpx

from promptgate.providers.upstream import _request_config
from promptgate.server import app


def test_missing_auth_is_rejected(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_UNSAFE_DEV_NO_AUTH", "false")
    response = TestClient(app).post("/v1/chat/completions", json={"messages": [{"content": "hello"}]})
    assert response.status_code == 401


def test_invalid_auth_is_rejected(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    response = TestClient(app).post("/v1/chat/completions", json={"messages": [{"content": "hello"}]}, headers={"Authorization": "Bearer wrong"})
    assert response.status_code == 401


def test_valid_auth_is_accepted(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"messages": [{"content": "hello"}]},
        headers={"Authorization": "Bearer local_promptgate_key"},
    )
    assert response.status_code == 200


def test_unsafe_dev_mode_must_be_explicit(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "")
    monkeypatch.setenv("PROMPTGATE_UNSAFE_DEV_NO_AUTH", "false")
    denied = TestClient(app).post("/v1/chat/completions", json={"messages": [{"content": "hello"}]})
    assert denied.status_code == 503

    monkeypatch.setenv("PROMPTGATE_UNSAFE_DEV_NO_AUTH", "true")
    allowed = TestClient(app).post("/v1/chat/completions", json={"messages": [{"content": "hello"}]})
    assert allowed.status_code == 200


def test_status_does_not_expose_secrets(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    monkeypatch.setenv("DEMO_EMAIL", "owner-demo@example.com")
    response = TestClient(app).get("/status")
    assert response.status_code == 200
    body = response.text
    assert "upstream-secret" not in body
    assert "local_promptgate_key" not in body
    assert "owner-demo@example.com" not in body


def test_models_endpoint_is_openai_compatible_and_sanitized(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_MODEL_LIST", "promptgate-live,gpt-demo")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    response = TestClient(app).get("/v1/models")
    assert response.status_code == 200
    payload = response.json()
    assert payload["object"] == "list"
    assert [model["id"] for model in payload["data"]] == ["promptgate-live", "gpt-demo"]
    assert "upstream-secret" not in response.text


def test_unversioned_models_and_chat_completion_alias(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    models = TestClient(app).get("/models")
    assert models.status_code == 200
    response = TestClient(app).post(
        "/chat/completions",
        json={"model": "promptgate-live", "messages": [{"role": "user", "content": "hello"}]},
        headers={"Authorization": "Bearer local_promptgate_key"},
    )
    assert response.status_code == 200


def test_upstream_forwarding_uses_rewritten_payload_and_hides_api_key(monkeypatch, caplog):
    captured = {}

    async def local_fake_upstream(endpoint, payload, base_url, api_key, http_proxy="", ca_bundle=""):
        captured["path"] = endpoint
        captured["auth"] = f"Bearer {api_key}"
        captured["payload"] = payload
        captured["base_url"] = base_url
        captured["http_proxy"] = http_proxy
        captured["ca_bundle"] = ca_bundle
        return {"ok": True, "choices": []}

    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "upstream")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_BASE_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_MODEL", "gpt-real")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_HTTP_PROXY", "http://127.0.0.1:8080")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_CA_BUNDLE", "/tmp/fake-ca.pem")
    monkeypatch.setattr("promptgate.server.forward", local_fake_upstream)
    caplog.set_level("INFO", logger="promptgate")

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"model": "promptgate-live", "messages": [{"content": "Email alice@example.com from 10.9.8.7"}]},
        headers={"Authorization": "Bearer local_promptgate_key"},
    )

    assert response.status_code == 200
    body = str(captured["payload"])
    assert "alice@example.com" not in body
    assert "10.9.8.7" not in body
    assert "PRIVATE_EMAIL" in body
    assert captured["payload"]["model"] == "gpt-real"
    assert captured["auth"] == "Bearer upstream-secret"
    assert captured["path"] == "/v1/chat/completions"
    assert captured["http_proxy"] == "http://127.0.0.1:8080"
    assert captured["ca_bundle"] == "/tmp/fake-ca.pem"
    assert "upstream-secret" not in caplog.text
    assert "http://127.0.0.1:8080" not in caplog.text

    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "mock")
    monkeypatch.delenv("PROMPTGATE_UPSTREAM_MODEL", raising=False)


def test_upstream_streaming_uses_rewritten_payload_and_hides_api_key(monkeypatch, caplog):
    captured = {}

    async def local_fake_upstream_stream(endpoint, payload, base_url, api_key, http_proxy="", ca_bundle=""):
        captured["path"] = endpoint
        captured["auth"] = f"Bearer {api_key}"
        captured["payload"] = payload
        yield b'data: {"choices":[{"delta":{"content":"ok"}}]}\n\n'
        yield b"data: [DONE]\n\n"

    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "upstream")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_BASE_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    monkeypatch.setenv("PROVIDER_MODEL", "gpt-real")
    monkeypatch.setattr("promptgate.server.forward_stream", local_fake_upstream_stream)
    caplog.set_level("INFO", logger="promptgate")

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"model": "promptgate-live", "stream": True, "messages": [{"content": "Email alice@example.com from 10.9.8.7"}]},
        headers={"Authorization": "Bearer local_promptgate_key"},
    )

    assert response.status_code == 200
    assert "data: [DONE]" in response.text
    body = str(captured["payload"])
    assert "alice@example.com" not in body
    assert "10.9.8.7" not in body
    assert "PRIVATE_EMAIL" in body
    assert captured["payload"]["model"] == "gpt-real"
    assert captured["auth"] == "Bearer upstream-secret"
    assert captured["path"] == "/v1/chat/completions"
    assert "upstream-secret" not in caplog.text

    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "mock")
    monkeypatch.delenv("PROVIDER_MODEL", raising=False)


def test_upstream_streaming_tls_error_is_sanitized(monkeypatch):
    async def failing_upstream_stream(endpoint, payload, base_url, api_key, http_proxy="", ca_bundle=""):
        raise httpx.ConnectError("[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed")
        yield b""

    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "upstream")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    monkeypatch.setattr("promptgate.server.forward_stream", failing_upstream_stream)

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"stream": True, "messages": [{"content": "hello"}]},
        headers={"Authorization": "Bearer local_promptgate_key"},
    )

    assert response.status_code == 200
    assert "PROMPTGATE_UPSTREAM_CA_BUNDLE" in response.text
    assert "upstream-secret" not in response.text

    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "mock")


def test_upstream_base_url_accepts_versioned_or_root_base():
    root_url, _, _ = _request_config("/v1/chat/completions", "https://api.openai.com", "key")
    versioned_url, _, _ = _request_config("/v1/chat/completions", "https://api.openai.com/v1", "key")

    assert root_url == "https://api.openai.com/v1/chat/completions"
    assert versioned_url == "https://api.openai.com/v1/chat/completions"
