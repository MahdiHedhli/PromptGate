from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    policy_path: Path
    provider_mode: str
    upstream_base_url: str
    upstream_api_key: str
    host: str
    port: int
    local_auth_token: str
    unsafe_dev_no_auth: bool


def current_settings() -> Settings:
    return Settings(
        policy_path=Path(os.getenv("PROMPTGATE_POLICY", "policies/default.yaml")),
        provider_mode=os.getenv("PROMPTGATE_PROVIDER_MODE", "mock"),
        upstream_base_url=os.getenv("PROMPTGATE_UPSTREAM_BASE_URL", ""),
        upstream_api_key=os.getenv("PROMPTGATE_UPSTREAM_API_KEY", ""),
        host=os.getenv("PROMPTGATE_HOST", "127.0.0.1"),
        port=int(os.getenv("PROMPTGATE_PORT", "8787")),
        local_auth_token=os.getenv("PROMPTGATE_AUTH_TOKEN", ""),
        unsafe_dev_no_auth=os.getenv("PROMPTGATE_UNSAFE_DEV_NO_AUTH", "false").lower() in {"1", "true", "yes"},
    )


settings = current_settings()
