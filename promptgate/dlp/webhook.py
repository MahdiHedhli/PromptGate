from __future__ import annotations

import httpx


class WebhookAdapter:
    def __init__(self, url: str, timeout: float = 2.0) -> None:
        self.url = url
        self.timeout = timeout

    async def load_rules(self) -> list[dict]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(self.url)
            response.raise_for_status()
            return response.json().get("rules", [])
