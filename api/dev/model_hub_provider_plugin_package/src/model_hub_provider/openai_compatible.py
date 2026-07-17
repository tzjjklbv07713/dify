"""OpenAI-compatible request / stream helpers for the model-hub provider package.

The proxy itself may route to Anthropic, Gemini, DeepSeek, Qwen, and others,
but from the plugin runtime perspective we only need a stable transport
contract. This helper normalizes that contract to a small OpenAI-compatible
shape so the future live plugin runtime can focus on Dify entity mapping.
"""

from __future__ import annotations

import json
from collections.abc import Generator, Iterable
from typing import Any


def build_chat_completions_payload(
    *,
    model: str,
    messages: list[dict[str, Any]],
    stream: bool,
    model_parameters: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
    stop: list[str] | None = None,
) -> dict[str, Any]:
    """Build the canonical OpenAI-compatible chat-completions payload."""

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": bool(stream),
    }
    if model_parameters:
        payload.update(model_parameters)
    if tools:
        payload["tools"] = tools
    if stop:
        payload["stop"] = stop
    return payload


def build_responses_payload(
    *,
    model: str,
    messages: list[dict[str, Any]],
    stream: bool,
    model_parameters: dict[str, Any] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build the canonical OpenAI Responses payload."""

    payload: dict[str, Any] = {
        "model": model,
        "input": messages,
        "stream": bool(stream),
    }
    if model_parameters:
        payload.update(model_parameters)
    if tools:
        payload["tools"] = tools
    return payload


def iter_openai_stream_events(lines: Iterable[str | bytes]) -> Generator[dict[str, Any], None, None]:
    """Parse SSE-style OpenAI-compatible stream lines into JSON events."""

    for raw_line in lines:
        if isinstance(raw_line, bytes):
            line = raw_line.decode("utf-8", errors="ignore").strip()
        else:
            line = str(raw_line).strip()

        if not line:
            continue
        if line.startswith("data:"):
            line = line[5:].strip()
        if not line or line == "[DONE]":
            continue

        payload = json.loads(line)
        if isinstance(payload, dict):
            yield payload


def build_tts_payload(
    *,
    model: str,
    content_text: str,
    voice: str,
    model_parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the canonical OpenAI-compatible text-to-speech payload."""

    payload: dict[str, Any] = {
        "model": model,
        "input": content_text,
        "voice": voice,
    }
    if model_parameters:
        payload.update(model_parameters)
    return payload


def build_speech_to_text_payload(
    *,
    model: str,
    file_name: str,
    file_bytes: bytes,
    content_type: str = "audio/wav",
    model_parameters: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, tuple[str, bytes, str]]]:
    """Build multipart payload for an OpenAI-compatible transcription request."""

    data: dict[str, Any] = {"model": model}
    if model_parameters:
        data.update(model_parameters)
    files = {
        "file": (file_name, file_bytes, content_type),
    }
    return data, files
