from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from dev.model_hub_provider_plugin_package.smoke_live import run_smoke


def test_run_smoke_collects_ping_catalog_and_reply() -> None:
    runtime = SimpleNamespace(
        validate_provider_credentials=lambda: {"ok": True},
        fetch_remote_models=lambda: [SimpleNamespace(model="gpt-5.5"), SimpleNamespace(model="claude-3-5-sonnet")],
        invoke_llm=lambda **_kwargs: SimpleNamespace(
            model="gpt-5.5",
            message=SimpleNamespace(content="OK"),
            usage=SimpleNamespace(total_tokens=12),
        ),
    )

    with patch("dev.model_hub_provider_plugin_package.smoke_live.ModelHubProviderRuntime", return_value=runtime):
        result = run_smoke(
            credentials={"proxy_base_url": "https://proxy.example.com", "proxy_api_key": "secret"},
            model="gpt-5.5",
            message="Please reply with OK only.",
        )

    assert result["provider_ping"] == {"ok": True}
    assert result["catalog_total"] == 2
    assert result["reply_text"] == "OK"
    assert result["usage_total_tokens"] == 12
