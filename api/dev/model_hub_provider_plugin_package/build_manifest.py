# ruff: noqa: T201

"""Build the plugin package manifest from the scaffold provider declaration.

This is a developer helper, not a production packaging entrypoint. It keeps the
JSON package manifest aligned with the Python provider scaffold while the real
plugin package is still under construction.
"""

from __future__ import annotations

import json
from pathlib import Path

from core.plugin.entities.plugin import PluginCategory, PluginDeclaration, PluginResourceRequirements
from core.tools.entities.common_entities import I18nObject
from dev.model_hub_provider_scaffold.provider_schema import build_model_hub_provider_entity


def build_manifest() -> PluginDeclaration:
    provider = build_model_hub_provider_entity()
    return PluginDeclaration(
        version="0.1.5",
        author="your-company",
        name="model-hub-provider",
        label=I18nObject(en_US="Model Hub Provider", zh_Hans="Model Hub Provider"),
        description=I18nObject(
            en_US="Custom model provider for a third-party proxy that aggregates multiple upstream model vendors.",
            zh_Hans="Custom model provider for a third-party proxy that aggregates multiple upstream model vendors.",
        ),
        icon="_assets/model-hub-icon.svg",
        icon_dark="_assets/model-hub-icon-dark.svg",
        created_at="2026-07-07T00:20:00+08:00",
        resource=PluginResourceRequirements(
            memory=268435456,
            permission=PluginResourceRequirements.Permission(
                model=PluginResourceRequirements.Permission.Model(
                    enabled=True,
                    llm=True,
                    text_embedding=True,
                    rerank=True,
                    tts=True,
                    speech2text=True,
                )
            ),
        ),
        plugins=PluginDeclaration.Plugins(models=[provider.provider]),
        tags=["model-hub", "proxy", "openai-compatible", "multi-vendor"],
        verified=False,
        model=provider,
        meta=PluginDeclaration.Meta(minimum_dify_version="1.15.0", version="0.1.5"),
        category=PluginCategory.Model,
    )


def main() -> None:
    manifest = build_manifest()
    target = Path(__file__).with_name("manifest.generated.json")
    target.write_text(json.dumps(manifest.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
