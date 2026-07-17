"""Runtime payload notes for the model-hub provider scaffold.

This module intentionally stops at payload-shaping helpers. The actual Dify
plugin runtime still needs to call the plugin daemon transport, but these
helpers lock down the contract we expect the proxy to support so the future
plugin implementation is less ambiguous.
"""

from __future__ import annotations

from typing import Any

from .entities import ModelHubProviderCredentials


def build_llm_invoke_payload(
    *,
    credentials: ModelHubProviderCredentials,
    model: str,
    messages: list[dict[str, Any]],
    stream: bool,
    model_parameters: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the canonical proxy payload for LLM invocation."""

    return {
        "model": model,
        "stream": bool(stream),
        "protocol": credentials.get("api_protocol", "responses"),
        "routing_group": credentials.get("routing_group") or None,
        "messages": messages,
        "model_parameters": model_parameters or {},
        "tools": tools or [],
    }
