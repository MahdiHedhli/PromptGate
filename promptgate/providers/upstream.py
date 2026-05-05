from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import urljoin, urlsplit

import httpx


class UpstreamConfigError(ValueError):
    pass


def _request_config(endpoint: str, base_url: str, api_key: str, http_proxy: str = "", ca_bundle: str = "") -> tuple[str, dict, dict]:
    if not base_url:
        raise UpstreamConfigError("PROMPTGATE_UPSTREAM_BASE_URL is required when provider mode is upstream")
    if not api_key:
        raise UpstreamConfigError("PROMPTGATE_UPSTREAM_API_KEY is required when provider mode is upstream")
    url = _join_upstream_url(base_url, endpoint)
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    client_args = {"timeout": 60}
    if http_proxy:
        client_args["proxy"] = http_proxy
    if ca_bundle:
        client_args["verify"] = ca_bundle
    return url, headers, client_args


def _join_upstream_url(base_url: str, endpoint: str) -> str:
    endpoint_path = endpoint.lstrip("/")
    base_path = urlsplit(base_url).path.rstrip("/")
    if base_path.endswith("/v1") and endpoint_path.startswith("v1/"):
        endpoint_path = endpoint_path.removeprefix("v1/")
    return urljoin(base_url.rstrip("/") + "/", endpoint_path)


async def forward(endpoint: str, payload: dict, base_url: str, api_key: str, http_proxy: str = "", ca_bundle: str = "") -> dict:
    url, headers, client_args = _request_config(endpoint, base_url, api_key, http_proxy, ca_bundle)
    async with httpx.AsyncClient(**client_args) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


def forward_stream(endpoint: str, payload: dict, base_url: str, api_key: str, http_proxy: str = "", ca_bundle: str = "") -> AsyncIterator[bytes]:
    url, headers, client_args = _request_config(endpoint, base_url, api_key, http_proxy, ca_bundle)

    async def body() -> AsyncIterator[bytes]:
        async with httpx.AsyncClient(**client_args) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes():
                    yield chunk

    return body()
