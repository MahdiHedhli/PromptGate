from __future__ import annotations

from copy import deepcopy

RECEIVED: list[dict] = []


def reset() -> None:
    RECEIVED.clear()


def received() -> list[dict]:
    return deepcopy(RECEIVED)


async def chat_completion(payload: dict) -> dict:
    RECEIVED.append(deepcopy(payload))
    return {
        "id": "promptgate-mock-chat",
        "object": "chat.completion",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": "mock response"}, "finish_reason": "stop"}],
    }


async def anthropic_message(payload: dict) -> dict:
    RECEIVED.append(deepcopy(payload))
    return {
        "id": "msg_promptgate_mock",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "mock response"}],
        "model": payload.get("model", "mock"),
        "stop_reason": "end_turn",
    }
