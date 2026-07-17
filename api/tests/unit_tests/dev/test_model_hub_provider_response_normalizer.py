from __future__ import annotations

from dev.model_hub_provider_plugin_package.src.model_hub_provider.response_normalizer import (
    iter_chat_completions_stream,
    normalize_chat_completions_response,
    normalize_responses_api_response,
)
from graphon.model_runtime.entities.message_entities import AssistantPromptMessage


def test_normalize_chat_completions_response_maps_message_and_usage() -> None:
    result = normalize_chat_completions_response(
        payload={
            "id": "chatcmpl-1",
            "model": "gpt-5.5",
            "choices": [
                {
                    "message": {
                        "content": "hello",
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        },
        fallback_model="fallback-model",
        prompt_messages=[],
    )

    assert result.model == "gpt-5.5"
    assert result.message.content == "hello"
    assert result.usage.total_tokens == 15


def test_normalize_responses_api_response_collects_text_output() -> None:
    result = normalize_responses_api_response(
        payload={
            "id": "resp-1",
            "model": "claude-3-5-sonnet",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "output_text", "text": "OK"},
                    ],
                }
            ],
        },
        fallback_model="fallback-model",
        prompt_messages=[],
    )

    assert result.model == "claude-3-5-sonnet"
    assert result.message.content == "OK"


def test_iter_chat_completions_stream_emits_delta_chunks() -> None:
    chunks = list(
        iter_chat_completions_stream(
            chunks=[
                {
                    "model": "gpt-5.5",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": "O"},
                        }
                    ],
                },
                {
                    "model": "gpt-5.5",
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": "K"},
                        }
                    ],
                },
            ],
            fallback_model="fallback-model",
            prompt_messages=[],
        )
    )

    assert len(chunks) == 2
    assert chunks[0].delta.message.content == "O"
    assert chunks[1].delta.message.content == "K"
    assert isinstance(chunks[0].delta.message, AssistantPromptMessage)
