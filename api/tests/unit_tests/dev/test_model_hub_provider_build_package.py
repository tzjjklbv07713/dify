from __future__ import annotations

import zipfile
from pathlib import Path

from dev.model_hub_provider_plugin_package.build_package import build_package


def test_build_package_creates_difypkg_with_manifest_and_assets(tmp_path: Path) -> None:
    output_path = tmp_path / "model-hub-provider.difypkg"

    built = build_package(output_path=output_path)

    assert built == output_path
    assert output_path.exists()

    with zipfile.ZipFile(output_path, "r") as archive:
        names = set(archive.namelist())

    assert "manifest.yaml" in names
    assert "README.md" in names
    assert "main.py" in names
    assert "provider/model_hub.yaml" in names
    assert "models/llm/llm.py" in names
    assert "_assets/model-hub-icon.svg" in names
    assert not any("__pycache__" in name for name in names)
    assert not any(name.endswith(".pyc") for name in names)
