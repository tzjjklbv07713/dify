"""Normalize OpenAI-compatible proxy responses into Dify runtime entities."""

from __future__ import annotations

from collections.abc import Generator, Iterable, Sequence
from decimal import Decimal
from typing import Any

from graphon.model_runtime.entities.llm_entities import LLMResult, LLMResultChunk, LLMResultChunkDelta, LLMUsage
from graphon.model_runtime.entities.message_entities import AssistantPromptMessage, PromptMessage


def _safe_decimal(value: Any) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return Decimal(0)


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _build_usage(payload: dict[str, Any] | None) -> LLMUsage:
    if not payload:
        return LLMUsage.empty_usage()

    prompt_tokens = _safe_int(payload.get("prompt_tokens"))
    completion_tokens = _safe_int(payload.get("completion_tokens"))
    total_tokens = _safe_int(payload.get("total_tokens")) or prompt_tokens + completion_tokens

    return LLMUsage(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        prompt_unit_price=Decimal(0),
        completion_unit_price=Decimal(0),
        prompt_price_unit=Decimal(0),
        prompt_price=Decimal(0),
        completion_price_unit=Decimal(0),
        completion_price=Decimal(0),
        total_price=Decimal(0),
        currency="USD",
        latency=_safe_decimal(payload.get("latency", 0)),
    )


def _build_tool_calls(tool_calls: Sequence[dict[str, Any]] | None) -> list[AssistantPromptMessage.ToolCall]:
    result: list[AssistantPromptMessage.ToolCall] = []
    for item in tool_calls or []:
        function = item.get("function") or {}
        name = str(function.get("name") or "").strip()
        arguments = function.get("arguments")
        if not name:
            continue
        result.append(
            AssistantPromptMessage.ToolCall(
                id=str(item.get("id") or ""),
                type=str(item.get("type") or "function"),
                function=AssistantPromptMessage.ToolCall.ToolCallFunction(
                    name=name,
                    arguments=str(arguments or "{}"),
                ),
            )
        )
    return result


def normalize_chat_completions_response(
    *,
    payload: dict[str, Any],
    fallback_model: str,
    prompt_messages: Sequence[PromptMessage],
) -> LLMResult:
    """Normalize a blocking OpenAI chat-completions response."""

    choices = payload.get("choices") or []
    first_choice = choices[0] if choices else {}
    message = first_choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, list):
        content = "".join(str(item.get("text") or "") for item in content if isinstance(item, dict))

    return LLMResult(
        id=str(payload.get("id") or ""),
        model=str(payload.get("model") or fallback_model),
        prompt_messages=list(prompt_messages),
        message=AssistantPromptMessage(
            content=str(content or ""),
            tool_calls=_build_tool_calls(message.get("tool_calls")),
        ),
        usage=_build_usage(payload.get("usage") or {}),
    )


def normalize_responses_api_response(
    *,
    payload: dict[str, Any],
    fallback_model: str,
    prompt_messages: Sequence[PromptMessage],
) -> LLMResult:
    """Normalize a blocking OpenAI Responses API response."""

    output = payload.get("output") or []
    text_parts: list[str] = []
    tool_calls: list[dict[str, Any]] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type")
        if item_type == "message":
            for content_item in item.get("content") or []:
                if isinstance(content_item, dict) and content_item.get("type") in {"output_text", "text"}:
                    text_parts.append(str(content_item.get("text") or ""))
        elif item_type in {"function_call", "tool_call"}:
            tool_calls.append(
                {
                    "id": item.get("call_id") or item.get("id"),
                    "type": "function",
                    "function": {
                        "name": item.get("name"),
                        "arguments": item.get("arguments") or "{}",
                    },
                }
            )

    return LLMResult(
        id=str(payload.get("id") or ""),
        model=str(payload.get("model") or fallback_model),
        prompt_messages=list(prompt_messages),
        message=AssistantPromptMessage(
            content="".join(text_parts),
            tool_calls=_build_tool_calls(tool_calls),
        ),
        usage=_build_usage(payload.get("usage") or {}),
    )


def iter_chat_completions_stream(
    *,
    chunks: Iterable[dict[str, Any]],
    fallback_model: str,
    prompt_messages: Sequence[PromptMessage],
) -> Generator[LLMResultChunk, None, None]:
    """Normalize an OpenAI chat-completions streaming sequence."""

    for chunk in chunks:
        choices = chunk.get("choices") or []
        first_choice = choices[0] if choices else {}
        delta = first_choice.get("delta") or {}
        content = delta.get("content")
        if isinstance(content, list):
            content = "".join(str(item.get("text") or "") for item in content if isinstance(item, dict))

        yield LLMResultChunk(
            model=str(chunk.get("model") or fallback_model),
            prompt_messages=list(prompt_messages),
            delta=LLMResultChunkDelta(
                index=_safe_int(first_choice.get("index", 0)),
                message=AssistantPromptMessage(
                    content=None if content is None else str(content),
                    tool_calls=_build_tool_calls(delta.get("tool_calls")),
                ),
                usage=_build_usage(chunk.get("usage") or {}),
            ),
        )


def iter_responses_api_stream(
    *,
    chunks: Iterable[dict[str, Any]],
    fallback_model: str,
    prompt_messages: Sequence[PromptMessage],
) -> Generator[LLMResultChunk, None, None]:
    """Normalize an OpenAI Responses API streaming sequence."""

    for chunk in chunks:
        event_type = str(chunk.get("type") or "")
        text_delta = ""
        tool_calls: list[dict[str, Any]] = []

        if event_type == "response.output_text.delta":
            text_delta = str(chunk.get("delta") or "")
        elif event_type in {"response.output_item.added", "response.function_call_arguments.delta"}:
            item = chunk.get("item") or {}
            if item and item.get("type") in {"function_call", "tool_call"}:
                tool_calls.append(
                    {
                        "id": item.get("call_id") or item.get("id"),
                        "type": "function",
                        "function": {
                            "name": item.get("name"),
                            "arguments": item.get("arguments") or "{}",
                        },
                    }
                )

        yield LLMResultChunk(
            model=str(chunk.get("model") or fallback_model),
            prompt_messages=list(prompt_messages),
            delta=LLMResultChunkDelta(
                index=0,
                message=AssistantPromptMessage(
                    content=text_delta,
                    tool_calls=_build_tool_calls(tool_calls),
                ),
                usage=_build_usage(chunk.get("usage") or {}),
            ),
        )
