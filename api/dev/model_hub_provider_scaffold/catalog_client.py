"""Proxy catalog / validation client for the model-hub provider scaffold.

This module is deliberately runtime-agnostic: it does not depend on Dify's
plugin daemon. The future plugin package can reuse the logic directly, or copy
the request / normalization flow into its plugin runtime implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from graphon.model_runtime.entities.common_entities import I18nObject
from graphon.model_runtime.entities.model_entities import (
    AIModelEntity,
    FetchFrom,
    ModelFeature,
    ModelPropertyKey,
    ModelType,
)

from .entities import ModelHubModelRecord, ModelHubModelsResponse, ModelHubProviderCredentials

_SUPPORTED_MODEL_TYPES: dict[str, ModelType] = {
    "llm": ModelType.LLM,
    "text-embedding": ModelType.TEXT_EMBEDDING,
    "rerank": ModelType.RERANK,
    "speech2text": ModelType.SPEECH2TEXT,
    "tts": ModelType.TTS,
}

_SUPPORTED_FEATURES: dict[str, ModelFeature] = {
    "tool-call": ModelFeature.TOOL_CALL,
    "multi-tool-call": ModelFeature.MULTI_TOOL_CALL,
    "stream-tool-call": ModelFeature.STREAM_TOOL_CALL,
    "structured-output": ModelFeature.STRUCTURED_OUTPUT,
    "vision": ModelFeature.VISION,
    "audio": ModelFeature.AUDIO,
    "video": ModelFeature.VIDEO,
    "document": ModelFeature.DOCUMENT,
    "agent-thought": ModelFeature.AGENT_THOUGHT,
    "polling": ModelFeature.POLLING,
}


@dataclass(slots=True)
class ModelHubCatalogClient:
    """Thin client around the proxy endpoints required by the provider plugin."""

    credentials: ModelHubProviderCredentials

    def _base_url(self) -> str:
        return str(self.credentials["proxy_base_url"]).strip().rstrip("/")

    def _timeout_ms(self) -> int:
        timeout_ms = int(self.credentials.get("timeout_ms", 15000) or 15000)
        return min(max(timeout_ms, 1000), 120000)

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.credentials['proxy_api_key']}",
        }

    def build_ping_url(self) -> str:
        return f"{self._base_url()}/provider/ping"

    def build_models_url(self) -> str:
        catalog_path = str(self.credentials.get("catalog_path", "/provider/models") or "/provider/models").strip()
        normalized = catalog_path if catalog_path.startswith("/") else f"/{catalog_path}"
        return f"{self._base_url()}{normalized}"

    def validate_credentials(self) -> dict[str, Any]:
        """Validate provider credentials against the proxy ping endpoint."""

        response = httpx.get(
            self.build_ping_url(),
            headers=self._headers(),
            timeout=self._timeout_ms() / 1000,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not payload.get("ok"):
            raise ValueError(f"model_hub_ping_failed:{payload}")
        return payload

    def fetch_models_payload(self) -> ModelHubModelsResponse:
        """Fetch the remote model catalog from the proxy."""

        response = httpx.get(
            self.build_models_url(),
            headers=self._headers(),
            timeout=self._timeout_ms() / 1000,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("models"), list):
            raise ValueError("model_hub_catalog_invalid")
        return payload  # type: ignore[return-value]

    def fetch_models(self) -> list[AIModelEntity]:
        """Normalize the proxy catalog into Dify model entities."""

        payload = self.fetch_models_payload()
        return [self._to_model_entity(item) for item in payload["models"]]

    def _to_model_entity(self, item: ModelHubModelRecord) -> AIModelEntity:
        model_type = _SUPPORTED_MODEL_TYPES.get(item["type"])
        if model_type is None:
            raise ValueError(f"unsupported_model_type:{item['type']}")

        features = [
            _SUPPORTED_FEATURES[feature] for feature in item.get("features", []) if feature in _SUPPORTED_FEATURES
        ]
        properties: dict[ModelPropertyKey, Any] = {}
        if model_type == ModelType.LLM:
            properties[ModelPropertyKey.MODE] = item.get("mode", "chat")
        if item.get("context_size"):
            properties[ModelPropertyKey.CONTEXT_SIZE] = item["context_size"]

        return AIModelEntity(
            model=item["id"],
            label=I18nObject(en_US=item.get("label", item["id"]), zh_Hans=item.get("label", item["id"])),
            model_type=model_type,
            fetch_from=FetchFrom.PREDEFINED_MODEL,
            model_properties=properties,
            features=features,
            deprecated=bool(item.get("deprecated", False)),
        )
