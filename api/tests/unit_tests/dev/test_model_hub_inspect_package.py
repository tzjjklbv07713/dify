from __future__ import annotations

from pathlib import Path

from dev.model_hub_provider_plugin_package.build_package import build_package
from dev.model_hub_provider_plugin_package.inspect_package import inspect_package


def test_inspect_package_reads_manifest_summary(tmp_path: Path) -> None:
    package_path = tmp_path / "model-hub-provider.difypkg"
    build_package(output_path=package_path)

    result = inspect_package(package_path)

    assert result["package"] == str(package_path)
    assert result["manifest"]["name"] == "model-hub-provider"
    assert "manifest.yaml" in result["entries"]
