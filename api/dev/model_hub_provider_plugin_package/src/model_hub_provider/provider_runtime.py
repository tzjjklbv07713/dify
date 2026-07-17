"""Provider-runtime scaffold for the model-hub plugin package.

This module is intentionally one layer closer to a real plugin runtime than the
generic scaffold under ``api/dev/model_hub_provider_scaffold``:

- it owns a concrete provider declaration
- it validates provider credentials against the proxy
- it resolves model schemas from the proxy catalog
- it exposes the minimal methods a future plugin daemon adapter would need

It still stops short of implementing Dify's final daemon packaging hooks.
"""

from __future__ import annotations

from collections.abc import Generator, Sequence
from dataclasses import dataclass
from typing import IO, Any

from dev.model_hub_provider_scaffold.catalog_client import ModelHubCatalogClient
from dev.model_hub_provider_scaffold.entities import ModelHubProviderCredentials
from dev.model_hub_provider_scaffold.provider_schema import PROVIDER_ID, build_model_hub_provider_entity
from graphon.model_runtime.entities.llm_entities import LLMResult, LLMResultChunk
from graphon.model_runtime.entities.message_entities import PromptMessage, PromptMessageTool
from graphon.model_runtime.entities.model_entities import AIModelEntity, ModelType
from graphon.model_runtime.entities.rerank_entities import RerankResult
from graphon.model_runtime.entities.text_embedding_entities import EmbeddingResult
from graphon.model_runtime.utils.encoders import jsonable_encoder

from .openai_compatible import (
    build_chat_completions_payload,
    build_responses_payload,
    build_speech_to_text_payload,
    build_tts_payload,
)
from .proxy_client import ModelHubProxyClient
from .response_normalizer import (
    iter_chat_completions_stream,
    iter_responses_api_stream,
    normalize_chat_completions_response,
    normalize_responses_api_response,
)
from .vector_normalizer import normalize_embedding_response, normalize_rerank_response


@dataclass(slots=True)
class ModelHubProviderRuntime:
    """Concrete runtime helper for the custom model-hub provider plugin."""

    credentials: ModelHubProviderCredentials

    @property
    def provider_id(self) -> str:
        return PROVIDER_ID

    def provider_entity(self):
        return build_model_hub_provider_entity()

    def validate_provider_credentials(self) -> dict[str, Any]:
        """Validate provider-level credentials against the proxy."""

        client = ModelHubCatalogClient(credentials=self.credentials)
        return client.validate_credentials()

    def validate_model_credentials(self, *, model_type: ModelType, model: str) -> dict[str, Any]:
        """Validate model-level access by checking the model exists in the catalog."""

        schema = self.get_model_schema(model_type=model_type, model=model)
        if schema is None:
            raise ValueError(f"model_not_found:{model_type.value}:{model}")
        return {"resolved_model": schema.model}

    def fetch_remote_models(self) -> list[AIModelEntity]:
        """Fetch and normalize the proxy model catalog."""

        client = ModelHubCatalogClient(credentials=self.credentials)
        return client.fetch_models()

    def get_model_schema(self, *, model_type: ModelType, model: str) -> AIModelEntity | None:
        """Resolve one model schema from the remote catalog."""

        for item in self.fetch_remote_models():
            if item.model_type == model_type and item.model == model:
                return item
        return None

    def invoke_llm(
        self,
        *,
        model: str,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict[str, Any] | None = None,
        tools: Sequence[PromptMessageTool] | None = None,
        stop: Sequence[str] | None = None,
        stream: bool = True,
    ) -> LLMResult | Generator[LLMResultChunk, None, None]:
        """Invoke the proxy through an OpenAI-compatible LLM endpoint."""

        protocol = str(self.credentials.get("api_protocol", "responses") or "responses").strip().lower()
        if protocol == "chat_completions":
            return self._invoke_chat_completions(
                model=model,
                prompt_messages=prompt_messages,
                model_parameters=model_parameters,
                tools=tools,
                stop=stop,
                stream=stream,
            )

        return self._invoke_responses(
            model=model,
            prompt_messages=prompt_messages,
            model_parameters=model_parameters,
            tools=tools,
            stream=stream,
        )

    def invoke_text_embedding(
        self,
        *,
        model: str,
        texts: Sequence[str],
        input_type: str | None = None,
    ) -> EmbeddingResult:
        """Invoke the proxy embedding endpoint."""

        client = self._proxy_client()
        payload: dict[str, Any] = {
            "model": model,
            "input": list(texts),
        }
        if input_type:
            payload["input_type"] = input_type
        return normalize_embedding_response(
            payload=client.post_json(path="/v1/embeddings", payload=payload),
            fallback_model=model,
        )

    def invoke_rerank(
        self,
        *,
        model: str,
        query: str,
        documents: Sequence[str],
        top_n: int | None = None,
    ) -> RerankResult:
        """Invoke the proxy rerank endpoint."""

        client = self._proxy_client()
        payload: dict[str, Any] = {
            "model": model,
            "query": query,
            "documents": list(documents),
        }
        if top_n is not None:
            payload["top_n"] = int(top_n)
        return normalize_rerank_response(
            payload=client.post_json(path="/v1/rerank", payload=payload),
            documents=list(documents),
            fallback_model=model,
        )

    def invoke_tts(
        self,
        *,
        model: str,
        content_text: str,
        voice: str,
        model_parameters: dict[str, Any] | None = None,
    ) -> Generator[bytes, None, None]:
        """Invoke the proxy text-to-speech endpoint."""

        client = self._proxy_client()
        payload = build_tts_payload(
            model=model,
            content_text=content_text,
            voice=voice,
            model_parameters=model_parameters,
        )
        audio_bytes = client.post_binary(path="/v1/audio/speech", payload=payload)

        def _generator() -> Generator[bytes, None, None]:
            yield audio_bytes

        return _generator()

    def get_tts_model_voices(
        self,
        *,
        model: str,
        language: str | None = None,
    ) -> list[dict[str, str]]:
        """Return placeholder voice metadata until the proxy exposes a voice catalog."""

        if language:
            return [{"name": f"{model}-{language}", "value": f"{model}-{language}"}]
        return [{"name": model, "value": model}]

    def invoke_speech_to_text(
        self,
        *,
        model: str,
        file: IO[bytes],
        filename: str = "audio.wav",
        content_type: str = "audio/wav",
        model_parameters: dict[str, Any] | None = None,
    ) -> str:
        """Invoke the proxy speech-to-text endpoint."""

        client = self._proxy_client()
        file_bytes = file.read()
        data, files = build_speech_to_text_payload(
            model=model,
            file_name=filename,
            file_bytes=file_bytes,
            content_type=content_type,
            model_parameters=model_parameters,
        )
        payload = client.post_multipart_json(path="/v1/audio/transcriptions", data=data, files=files)
        return str(payload.get("text") or payload.get("result") or "").strip()

    def _proxy_client(self) -> ModelHubProxyClient:
        return ModelHubProxyClient(credentials=self.credentials)

    def _invoke_chat_completions(
        self,
        *,
        model: str,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict[str, Any] | None,
        tools: Sequence[PromptMessageTool] | None,
        stop: Sequence[str] | None,
        stream: bool,
    ) -> LLMResult | Generator[LLMResultChunk, None, None]:
        payload = build_chat_completions_payload(
            model=model,
            messages=jsonable_encoder(list(prompt_messages)),
            stream=stream,
            model_parameters=model_parameters,
            tools=jsonable_encoder(list(tools)) if tools else None,
            stop=list(stop) if stop else None,
        )
        client = self._proxy_client()

        if not stream:
            return normalize_chat_completions_response(
                payload=client.post_json(path="/v1/chat/completions", payload=payload),
                fallback_model=model,
                prompt_messages=prompt_messages,
            )

        def _generator() -> Generator[LLMResultChunk, None, None]:
            events = client.post_stream(path="/v1/chat/completions", payload=payload)
            yield from iter_chat_completions_stream(
                chunks=events,
                fallback_model=model,
                prompt_messages=prompt_messages,
            )

        return _generator()

    def _invoke_responses(
        self,
        *,
        model: str,
        prompt_messages: Sequence[PromptMessage],
        model_parameters: dict[str, Any] | None,
        tools: Sequence[PromptMessageTool] | None,
        stream: bool,
    ) -> LLMResult | Generator[LLMResultChunk, None, None]:
        payload = build_responses_payload(
            model=model,
            messages=jsonable_encoder(list(prompt_messages)),
            stream=stream,
            model_parameters=model_parameters,
            tools=jsonable_encoder(list(tools)) if tools else None,
        )
        client = self._proxy_client()

        if not stream:
            return normalize_responses_api_response(
                payload=client.post_json(path="/v1/responses", payload=payload),
                fallback_model=model,
                prompt_messages=prompt_messages,
            )

        def _generator() -> Generator[LLMResultChunk, None, None]:
            events = client.post_stream(path="/v1/responses", payload=payload)
            yield from iter_responses_api_stream(
                chunks=events,
                fallback_model=model,
                prompt_messages=prompt_messages,
            )

        return _generator()
