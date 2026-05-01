import logging

from fastapi.testclient import TestClient

from promptgate.providers import mock
from promptgate.server import app


def test_mock_provider_egress_proof():
    client = TestClient(app)
    mock.reset()
    payload = {"model": "mock", "messages": [{"role": "user", "content": "Email alice@example.com from 10.1.2.3"}]}
    response = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer local_promptgate_key"})
    assert response.status_code == 200
    received = mock.received()
    body = str(received)
    assert "alice@example.com" not in body
    assert "10.1.2.3" not in body
    assert "PRIVATE_EMAIL" in body


def test_blocked_secret_never_reaches_provider():
    client = TestClient(app)
    mock.reset()
    payload = {"model": "mock", "messages": [{"role": "user", "content": "Use sk-abc1234567890SECRET"}]}
    response = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer local_promptgate_key"})
    assert response.status_code == 400
    assert mock.received() == []


def test_allowed_benign_reaches_provider():
    client = TestClient(app)
    mock.reset()
    payload = {"model": "mock", "messages": [{"role": "user", "content": "Summarize public docs"}]}
    response = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer local_promptgate_key"})
    assert response.status_code == 200
    assert "Summarize public docs" in str(mock.received())


def test_logs_do_not_contain_raw_sensitive_values(caplog):
    client = TestClient(app)
    mock.reset()
    caplog.set_level(logging.INFO, logger="promptgate")
    payload = {"model": "mock", "messages": [{"role": "user", "content": "Email alice@example.com"}]}
    response = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer local_promptgate_key"})
    assert response.status_code == 200
    assert "alice@example.com" not in caplog.text


def test_streaming_rejected_without_forwarding():
    client = TestClient(app)
    mock.reset()
    payload = {"model": "mock", "stream": True, "messages": [{"role": "user", "content": "Email alice@example.com"}]}
    response = client.post("/v1/chat/completions", json=payload, headers={"Authorization": "Bearer local_promptgate_key"})
    assert response.status_code == 400
    assert "streaming" in response.text
    assert mock.received() == []
