"""Typed payloads for the custom model-hub provider scaffold.

The real proxy can return extra metadata, but the scaffold keeps the required
surface intentionally small so the first implementation can focus on:

- credential validation via ``GET /provider/ping``
- model discovery via ``GET /provider/models``
- type / feature normalization into Dify runtime entities
"""

from __future__ import annotations

from typing import Literal, NotRequired, TypedDict

ModelHubModelType = Literal["llm", "text-embedding", "rerank", "speech2text", "tts"]


class ModelHubModelRecord(TypedDict):
    """Single model row returned by the proxy catalog endpoint."""

    id: str
    type: ModelHubModelType
    label: NotRequired[str]
    context_size: NotRequired[int]
    features: NotRequired[list[str]]
    mode: NotRequired[Literal["chat", "completion"]]
    deprecated: NotRequired[bool]


class ModelHubModelsResponse(TypedDict):
    """Canonical response shape for ``GET /provider/models``."""

    models: list[ModelHubModelRecord]


class ModelHubPingResponse(TypedDict):
    """Minimal successful response shape for ``GET /provider/ping``."""

    ok: bool
    provider: NotRequired[str]
    message: NotRequired[str]


class ModelHubProviderCredentials(TypedDict):
    """Provider-level credentials shown in the Dify credential form."""

    proxy_base_url: str
    proxy_api_key: str
    catalog_path: NotRequired[str]
    api_protocol: NotRequired[Literal["responses", "chat_completions"]]
    routing_group: NotRequired[str]
    timeout_ms: NotRequired[int]
    validation_model: NotRequired[str]
