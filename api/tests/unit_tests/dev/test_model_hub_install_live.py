from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from dev.model_hub_provider_plugin_package.install_live import run_install


def test_run_install_returns_decode_metadata(tmp_path: Path) -> None:
    package_path = tmp_path / "model-hub-provider.difypkg"
    package_path.write_bytes(b"fake-package")

    with (
        patch("dev.model_hub_provider_plugin_package.install_live._resolve_tenant_id", return_value="tenant-1"),
        patch(
            "dev.model_hub_provider_plugin_package.install_live.PluginService.upload_pkg",
            return_value=SimpleNamespace(
                unique_identifier="your-company/model-hub-provider:0.1.0@test",
                manifest=SimpleNamespace(name="model-hub-provider", author="your-company"),
            ),
        ),
    ):
        result = run_install(
            email="admin@bblizhuo.local",
            package_path=package_path,
            verify_signature=False,
            mode="decode",
        )

    assert result["tenant_id"] == "tenant-1"
    assert result["manifest_name"] == "model-hub-provider"
    assert result["manifest_author"] == "your-company"
