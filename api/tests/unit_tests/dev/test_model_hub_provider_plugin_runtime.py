from __future__ import annotations

from io import BytesIO
from unittest.mock import Mock, patch

import pytest

from dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime import ModelHubProviderRuntime
from graphon.model_runtime.entities.common_entities import I18nObject
from graphon.model_runtime.entities.model_entities import AIModelEntity, FetchFrom, ModelType
from graphon.model_runtime.entities.rerank_entities import RerankResult
from graphon.model_runtime.entities.text_embedding_entities import EmbeddingResult


def _mock_model(model: str, model_type: ModelType) -> AIModelEntity:
    return AIModelEntity(
        model=model,
        label=I18nObject(en_US=model),
        model_type=model_type,
        fetch_from=FetchFrom.PREDEFINED_MODEL,
        model_properties={},
    )


def test_runtime_provider_id_matches_declared_provider() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    assert runtime.provider_id == "your-company/model-hub/proxy"


def test_runtime_validates_provider_credentials_via_catalog_client() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubCatalogClient.validate_credentials",
        return_value={"ok": True},
    ) as mock_validate:
        result = runtime.validate_provider_credentials()

    assert result == {"ok": True}
    mock_validate.assert_called_once()


def test_runtime_get_model_schema_resolves_remote_model() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch.object(
        ModelHubProviderRuntime, "fetch_remote_models", return_value=[_mock_model("claude-3-5-sonnet", ModelType.LLM)]
    ):
        result = runtime.get_model_schema(model_type=ModelType.LLM, model="claude-3-5-sonnet")

    assert result is not None
    assert result.model == "claude-3-5-sonnet"


def test_runtime_validate_model_credentials_raises_for_missing_model() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch.object(ModelHubProviderRuntime, "fetch_remote_models", return_value=[]):
        with pytest.raises(ValueError, match="model_not_found"):
            runtime.validate_model_credentials(model_type=ModelType.LLM, model="missing-model")


def test_runtime_invoke_llm_chat_completions_blocking() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
            "api_protocol": "chat_completions",
        }
    )

    response = Mock()
    response.json.return_value = {
        "id": "chatcmpl-1",
        "model": "gpt-5.5",
        "choices": [{"message": {"content": "hello"}}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    response.raise_for_status.return_value = None

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_json",
        return_value=response.json.return_value,
    ):
        result = runtime.invoke_llm(model="gpt-5.5", prompt_messages=[], stream=False)

    assert result.message.content == "hello"
    assert result.model == "gpt-5.5"


def test_runtime_invoke_llm_responses_streaming() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
            "api_protocol": "responses",
        }
    )

    stream_response = Mock()
    stream_response.raise_for_status.return_value = None
    stream_response.iter_lines.return_value = [
        'data: {"type":"response.output_text.delta","delta":"O","model":"gpt-5.5"}',
        'data: {"type":"response.output_text.delta","delta":"K","model":"gpt-5.5"}',
        "data: [DONE]",
    ]
    stream_context = Mock()
    stream_context.__enter__ = Mock(return_value=stream_response)
    stream_context.__exit__ = Mock(return_value=None)

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_stream",
        return_value=[
            {"type": "response.output_text.delta", "delta": "O", "model": "gpt-5.5"},
            {"type": "response.output_text.delta", "delta": "K", "model": "gpt-5.5"},
        ],
    ):
        chunks = list(runtime.invoke_llm(model="gpt-5.5", prompt_messages=[], stream=True))

    assert len(chunks) == 2
    assert chunks[0].delta.message.content == "O"
    assert chunks[1].delta.message.content == "K"


def test_runtime_invoke_text_embedding() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_json",
        return_value={
            "model": "text-embedding-3-large",
            "data": [{"embedding": [0.1, 0.2]}],
            "usage": {"prompt_tokens": 2, "total_tokens": 2},
        },
    ):
        result = runtime.invoke_text_embedding(model="text-embedding-3-large", texts=["hello"])

    assert isinstance(result, EmbeddingResult)
    assert result.embeddings == [[0.1, 0.2]]


def test_runtime_invoke_rerank() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_json",
        return_value={
            "model": "rerank-v1",
            "results": [{"index": 0, "relevance_score": 0.88}],
        },
    ):
        result = runtime.invoke_rerank(model="rerank-v1", query="hello", documents=["doc-0"])

    assert isinstance(result, RerankResult)
    assert result.docs[0].score == 0.88


def test_runtime_invoke_tts() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_binary",
        return_value=b"audio-bytes",
    ):
        result = list(runtime.invoke_tts(model="gpt-4o-mini-tts", content_text="hello", voice="alloy"))

    assert result == [b"audio-bytes"]


def test_runtime_invoke_speech_to_text() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_multipart_json",
        return_value={"text": "transcribed text"},
    ):
        result = runtime.invoke_speech_to_text(
            model="gpt-4o-mini-transcribe",
            file=BytesIO(b"audio"),
            filename="audio.wav",
            content_type="audio/wav",
        )

    assert result == "transcribed text"
