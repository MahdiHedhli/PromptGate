from fastapi.testclient import TestClient

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


def test_status_does_not_expose_secrets(monkeypatch):
    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    response = TestClient(app).get("/status")
    assert response.status_code == 200
    body = response.text
    assert "upstream-secret" not in body
    assert "local_promptgate_key" not in body


def test_upstream_forwarding_uses_rewritten_payload_and_hides_api_key(monkeypatch, caplog):
    captured = {}

    async def local_fake_upstream(endpoint, payload, base_url, api_key):
        captured["path"] = endpoint
        captured["auth"] = f"Bearer {api_key}"
        captured["payload"] = payload
        captured["base_url"] = base_url
        return {"ok": True, "choices": []}

    monkeypatch.setenv("PROMPTGATE_AUTH_TOKEN", "local_promptgate_key")
    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "upstream")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_BASE_URL", "http://127.0.0.1:9999")
    monkeypatch.setenv("PROMPTGATE_UPSTREAM_API_KEY", "upstream-secret")
    monkeypatch.setattr("promptgate.server.forward", local_fake_upstream)
    caplog.set_level("INFO", logger="promptgate")

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"messages": [{"content": "Email alice@example.com from 10.9.8.7"}]},
        headers={"Authorization": "Bearer local_promptgate_key"},
    )

    assert response.status_code == 200
    body = str(captured["payload"])
    assert "alice@example.com" not in body
    assert "10.9.8.7" not in body
    assert "PRIVATE_EMAIL" in body
    assert captured["auth"] == "Bearer upstream-secret"
    assert captured["path"] == "/v1/chat/completions"
    assert "upstream-secret" not in caplog.text

    monkeypatch.setenv("PROMPTGATE_PROVIDER_MODE", "mock")
