from __future__ import annotations

from io import BytesIO
from unittest.mock import patch

from dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime import ModelHubProviderRuntime
from graphon.model_runtime.entities.common_entities import I18nObject
from graphon.model_runtime.entities.message_entities import UserPromptMessage
from graphon.model_runtime.entities.model_entities import AIModelEntity, FetchFrom, ModelType


def _model(name: str, model_type: ModelType) -> AIModelEntity:
    return AIModelEntity(
        model=name,
        label=I18nObject(en_US=name),
        model_type=model_type,
        fetch_from=FetchFrom.PREDEFINED_MODEL,
        model_properties={},
    )


def test_end_to_end_mock_runtime_for_all_supported_capabilities() -> None:
    runtime = ModelHubProviderRuntime(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
            "api_protocol": "responses",
        }
    )

    fake_models = [
        _model("gpt-5.5", ModelType.LLM),
        _model("text-embedding-3-large", ModelType.TEXT_EMBEDDING),
        _model("rerank-v1", ModelType.RERANK),
        _model("gpt-4o-mini-tts", ModelType.TTS),
        _model("gpt-4o-mini-transcribe", ModelType.SPEECH2TEXT),
    ]

    with (
        patch.object(ModelHubProviderRuntime, "fetch_remote_models", return_value=fake_models),
        patch(
            "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_json",
            side_effect=[
                {
                    "id": "resp-1",
                    "model": "gpt-5.5",
                    "output": [{"type": "message", "content": [{"type": "output_text", "text": "OK"}]}],
                },
                {
                    "model": "text-embedding-3-large",
                    "data": [{"embedding": [0.1, 0.2]}],
                    "usage": {"tokens": 2, "total_tokens": 2},
                },
                {
                    "model": "rerank-v1",
                    "results": [{"index": 0, "relevance_score": 0.91}],
                },
            ],
        ),
        patch(
            "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_binary",
            return_value=b"audio-bytes",
        ),
        patch(
            "dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime.ModelHubProxyClient.post_multipart_json",
            return_value={"text": "transcribed text"},
        ),
    ):
        llm_result = runtime.invoke_llm(
            model="gpt-5.5",
            prompt_messages=[UserPromptMessage(content="Please reply with OK only.")],
            stream=False,
        )
        embedding_result = runtime.invoke_text_embedding(model="text-embedding-3-large", texts=["hello"])
        rerank_result = runtime.invoke_rerank(model="rerank-v1", query="hello", documents=["doc-0"])
        tts_result = list(runtime.invoke_tts(model="gpt-4o-mini-tts", content_text="hello", voice="alloy"))
        stt_result = runtime.invoke_speech_to_text(
            model="gpt-4o-mini-transcribe",
            file=BytesIO(b"audio"),
            filename="audio.wav",
            content_type="audio/wav",
        )

    assert llm_result.message.content == "OK"
    assert embedding_result.embeddings == [[0.1, 0.2]]
    assert rerank_result.docs[0].score == 0.91
    assert tts_result == [b"audio-bytes"]
    assert stt_result == "transcribed text"
