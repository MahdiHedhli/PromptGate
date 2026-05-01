from __future__ import annotations

import httpx


async def forward_json(url: str, payload: dict, headers: dict[str, str] | None = None) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(url, json=payload, headers=headers or {})
        response.raise_for_status()
        return response.json()
