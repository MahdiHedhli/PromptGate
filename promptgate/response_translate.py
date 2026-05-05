from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from promptgate.redact import TokenVault

ROLLING_BUFFER_CHARS = 256


def translate_json_response(value: Any, vault: TokenVault, conversation_id: str) -> Any:
    if isinstance(value, str):
        return vault.restore(value, conversation_id)
    if isinstance(value, list):
        return [translate_json_response(item, vault, conversation_id) for item in value]
    if isinstance(value, dict):
        return {key: translate_json_response(item, vault, conversation_id) for key, item in value.items()}
    return value


async def translate_sse_stream(chunks: AsyncIterator[bytes], vault: TokenVault, conversation_id: str) -> AsyncIterator[bytes]:
    carry = ""
    async for chunk in chunks:
        text = chunk.decode("utf-8")
        combined = carry + text
        if len(combined) <= ROLLING_BUFFER_CHARS:
            carry = combined
            continue
        ready = combined[:-ROLLING_BUFFER_CHARS]
        carry = combined[-ROLLING_BUFFER_CHARS:]
        translated = vault.restore(ready, conversation_id)
        if translated:
            yield translated.encode("utf-8")
    if carry:
        translated = vault.restore(carry, conversation_id)
        if translated:
            yield translated.encode("utf-8")
