from __future__ import annotations

from unittest.mock import Mock, patch

from dev.model_hub_provider_plugin_package.src.model_hub_provider.proxy_client import ModelHubProxyClient


def test_proxy_client_post_json_returns_object_payload() -> None:
    client = ModelHubProxyClient(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )
    response = Mock()
    response.json.return_value = {"ok": True}
    response.raise_for_status.return_value = None

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.proxy_client.httpx.post", return_value=response
    ) as mock_post:
        result = client.post_json(path="/v1/responses", payload={"model": "gpt-5.5"})

    assert result == {"ok": True}
    assert mock_post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret"


def test_proxy_client_post_stream_yields_parsed_events() -> None:
    client = ModelHubProxyClient(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )

    stream_response = Mock()
    stream_response.raise_for_status.return_value = None
    stream_response.iter_lines.return_value = [
        'data: {"type":"response.output_text.delta","delta":"O"}',
        "data: [DONE]",
    ]
    stream_context = Mock()
    stream_context.__enter__ = Mock(return_value=stream_response)
    stream_context.__exit__ = Mock(return_value=None)

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.proxy_client.httpx.stream",
        return_value=stream_context,
    ):
        result = list(client.post_stream(path="/v1/responses", payload={"model": "gpt-5.5"}))

    assert result == [{"type": "response.output_text.delta", "delta": "O"}]


def test_proxy_client_post_binary_returns_raw_content() -> None:
    client = ModelHubProxyClient(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )
    response = Mock()
    response.content = b"audio-bytes"
    response.raise_for_status.return_value = None

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.proxy_client.httpx.post", return_value=response
    ):
        result = client.post_binary(path="/v1/audio/speech", payload={"model": "tts"})

    assert result == b"audio-bytes"


def test_proxy_client_post_multipart_json_returns_object_payload() -> None:
    client = ModelHubProxyClient(
        credentials={
            "proxy_base_url": "https://proxy.example.com",
            "proxy_api_key": "secret",
        }
    )
    response = Mock()
    response.json.return_value = {"text": "hello"}
    response.raise_for_status.return_value = None

    with patch(
        "dev.model_hub_provider_plugin_package.src.model_hub_provider.proxy_client.httpx.post", return_value=response
    ):
        result = client.post_multipart_json(
            path="/v1/audio/transcriptions",
            data={"model": "stt"},
            files={"file": ("audio.wav", b"abc", "audio/wav")},
        )

    assert result == {"text": "hello"}
