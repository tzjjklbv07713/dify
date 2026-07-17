"""Shared HTTP client for the model-hub provider runtime."""

from __future__ import annotations

from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import httpx

from dev.model_hub_provider_scaffold.entities import ModelHubProviderCredentials

from .openai_compatible import iter_openai_stream_events


@dataclass(slots=True)
class ModelHubProxyClient:
    """Minimal typed client around the proxy endpoints used by the provider."""

    credentials: ModelHubProviderCredentials

    def base_url(self) -> str:
        return str(self.credentials["proxy_base_url"]).strip().rstrip("/")

    def timeout_seconds(self) -> float:
        timeout_ms = int(self.credentials.get("timeout_ms", 15000) or 15000)
        timeout_ms = min(max(timeout_ms, 1000), 120000)
        return timeout_ms / 1000

    def headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.credentials['proxy_api_key']}",
            "Content-Type": "application/json",
        }

    def post_json(self, *, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self.base_url()}{path}",
            headers=self.headers(),
            json=payload,
            timeout=self.timeout_seconds(),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError("proxy_json_response_must_be_object")
        return data

    def post_stream(self, *, path: str, payload: dict[str, Any]) -> Generator[dict[str, Any], None, None]:
        with httpx.stream(
            "POST",
            f"{self.base_url()}{path}",
            headers=self.headers(),
            json=payload,
            timeout=self.timeout_seconds(),
        ) as response:
            response.raise_for_status()
            yield from iter_openai_stream_events(response.iter_lines())

    def post_json_list(self, *, path: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        response = httpx.post(
            f"{self.base_url()}{path}",
            headers=self.headers(),
            json=payload,
            timeout=self.timeout_seconds(),
        )
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("proxy_json_response_must_be_list")
        return [item for item in data if isinstance(item, dict)]

    def post_binary(self, *, path: str, payload: dict[str, Any]) -> bytes:
        response = httpx.post(
            f"{self.base_url()}{path}",
            headers=self.headers(),
            json=payload,
            timeout=self.timeout_seconds(),
        )
        response.raise_for_status()
        return response.content

    def post_multipart_json(
        self, *, path: str, data: dict[str, Any], files: dict[str, tuple[str, bytes, str]]
    ) -> dict[str, Any]:
        headers = self.headers().copy()
        headers.pop("Content-Type", None)
        response = httpx.post(
            f"{self.base_url()}{path}",
            headers=headers,
            data=data,
            files=files,
            timeout=self.timeout_seconds(),
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("proxy_json_response_must_be_object")
        return payload
