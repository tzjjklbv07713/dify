from __future__ import annotations

import json
from pathlib import Path

from core.plugin.entities.plugin import PluginCategory, PluginDeclaration


def test_model_hub_plugin_package_manifest_matches_plugin_declaration_schema() -> None:
    manifest_path = Path(__file__).resolve().parents[3] / "dev" / "model_hub_provider_plugin_package" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    declaration = PluginDeclaration.model_validate(manifest)

    assert declaration.author == "your-company"
    assert declaration.name == "model-hub-provider"
    assert declaration.version == "0.1.5"
    assert declaration.category == PluginCategory.Model
    assert declaration.model is not None
    assert declaration.model.provider == "your-company/model-hub/proxy"


def test_model_hub_plugin_daemon_manifest_exists() -> None:
    manifest_path = Path(__file__).resolve().parents[3] / "dev" / "model_hub_provider_plugin_package" / "manifest.yaml"
    assert manifest_path.exists()
