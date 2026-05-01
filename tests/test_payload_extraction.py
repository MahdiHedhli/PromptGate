from fastapi.testclient import TestClient

from promptgate.providers import mock
from promptgate.server import app

AUTH = {"Authorization": "Bearer local_promptgate_key"}


def _post(payload):
    client = TestClient(app)
    mock.reset()
    response = client.post("/v1/chat/completions", json=payload, headers=AUTH)
    assert response.status_code == 200, response.text
    body = str(mock.received())
    assert "alice@example.com" not in body
    assert "10.9.8.7" not in body
    assert "Project Raven" not in body
    return body


def test_openai_string_content_rewritten():
    body = _post({"model": "mock", "messages": [{"role": "user", "content": "alice@example.com 10.9.8.7 Project Raven"}]})
    assert "PRIVATE_EMAIL" in body


def test_openai_content_blocks_rewritten():
    body = _post(
        {
            "model": "mock",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Email alice@example.com"},
                        {"type": "text", "text": "IP 10.9.8.7"},
                    ],
                }
            ],
        }
    )
    assert "PRIVATE_EMAIL" in body and "IP_ADDRESS" in body


def test_responses_style_fields_rewritten():
    body = _post(
        {
            "model": "mock",
            "instructions": "Do not expose Project Raven",
            "input": [{"role": "user", "content": [{"type": "input_text", "text": "alice@example.com"}]}],
            "metadata": {"ticket": "source 10.9.8.7"},
        }
    )
    assert "CODENAME" in body and "PRIVATE_EMAIL" in body and "IP_ADDRESS" in body


def test_tool_arguments_outputs_and_mcp_results_rewritten():
    body = _post(
        {
            "model": "mock",
            "messages": [
                {
                    "role": "assistant",
                    "tool_calls": [
                        {
                            "type": "function",
                            "function": {
                                "name": "lookup",
                                "arguments": "{\"email\":\"alice@example.com\",\"ip\":\"10.9.8.7\"}",
                            },
                        }
                    ],
                },
                {"role": "tool", "content": "tool output for Project Raven"},
            ],
            "mcp": {"tool_result": {"content": [{"type": "text", "text": "alice@example.com"}]}},
        }
    )
    assert "PRIVATE_EMAIL" in body and "IP_ADDRESS" in body and "CODENAME" in body
    assert '"email":"[PRIVATE_EMAIL' in body or '\\"email\\":\\"[PRIVATE_EMAIL' in body or "'email': '[PRIVATE_EMAIL" in body


def test_anthropic_text_blocks_rewritten():
    client = TestClient(app)
    mock.reset()
    payload = {"model": "mock", "messages": [{"role": "user", "content": [{"type": "text", "text": "alice@example.com 10.9.8.7"}]}]}
    response = client.post("/v1/messages", json=payload, headers=AUTH)
    assert response.status_code == 200, response.text
    body = str(mock.received())
    assert "alice@example.com" not in body
    assert "10.9.8.7" not in body
    assert "PRIVATE_EMAIL" in body


def test_secret_in_nested_field_blocks_forwarding():
    client = TestClient(app)
    mock.reset()
    payload = {"model": "mock", "messages": [{"role": "user", "content": [{"type": "text", "text": "sk-abc1234567890SECRET"}]}]}
    response = client.post("/v1/chat/completions", json=payload, headers=AUTH)
    assert response.status_code == 400
    assert mock.received() == []
