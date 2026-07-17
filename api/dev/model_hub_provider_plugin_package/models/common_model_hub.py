"""Shared helpers for the daemon-installable model hub plugin package."""

from __future__ import annotations

from collections.abc import Mapping
from json import JSONDecodeError

import requests
from dify_plugin.errors.model import CredentialsValidateFailedError

_MODELS_TIMEOUT = (10, 30)


def _base_url(credentials: Mapping) -> str:
    return str(credentials.get("endpoint_url") or "").rstrip("/")


def _auth_headers(credentials: Mapping) -> dict[str, str]:
    api_key = str(credentials.get("api_key") or "").strip()
    return {"Authorization": f"Bearer {api_key}"} if api_key else {}


def _catalog_path(credentials: Mapping) -> str:
    path = str(credentials.get("catalog_path") or "/models").strip()
    return path if path.startswith("/") else f"/{path}"


def list_remote_models(credentials: Mapping) -> list[dict]:
    base = _base_url(credentials)
    if not base:
        return []

    response = requests.get(
        f"{base}{_catalog_path(credentials)}",
        headers=_auth_headers(credentials),
        timeout=_MODELS_TIMEOUT,
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except JSONDecodeError as error:
        raise CredentialsValidateFailedError(
            "The model catalog returned HTML instead of JSON. "
            "For OpenAI-compatible services, use a base URL ending in '/v1' and catalog path '/models'."
        ) from error
    items = None
    if isinstance(payload, dict):
        items = payload.get("models")
        if items is None:
            items = payload.get("data")
    else:
        items = payload
    if not isinstance(items, list):
        raise CredentialsValidateFailedError("The model catalog response does not contain a model list.")

    models: list[dict] = []
    for item in items:
        if isinstance(item, str):
            models.append({"id": item})
        elif isinstance(item, dict):
            models.append(item)
    return models


def assert_model_available(model: str, credentials: Mapping) -> None:
    try:
        models = list_remote_models(credentials)
    except Exception:
        return

    ids = [str(item.get("model") or item.get("id") or "").strip() for item in models]
    ids = [item for item in ids if item]
    if not ids or model in ids:
        return

    preview = ", ".join(ids[:50])
    suffix = " ..." if len(ids) > 50 else ""
    raise CredentialsValidateFailedError(
        f"Model '{model}' was not found on the model hub. Available models: {preview}{suffix}"
    )
