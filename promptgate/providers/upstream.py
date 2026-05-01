from __future__ import annotations

from urllib.parse import urljoin

import httpx


class UpstreamConfigError(ValueError):
    pass


async def forward(endpoint: str, payload: dict, base_url: str, api_key: str, http_proxy: str = "", ca_bundle: str = "") -> dict:
    if not base_url:
        raise UpstreamConfigError("PROMPTGATE_UPSTREAM_BASE_URL is required when provider mode is upstream")
    if not api_key:
        raise UpstreamConfigError("PROMPTGATE_UPSTREAM_API_KEY is required when provider mode is upstream")
    url = urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    client_args = {"timeout": 60}
    if http_proxy:
        client_args["proxy"] = http_proxy
    if ca_bundle:
        client_args["verify"] = ca_bundle
    async with httpx.AsyncClient(**client_args) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
