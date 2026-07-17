# ruff: noqa: T201

"""Inspect a built `.difypkg` archive and validate its daemon manifest."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import yaml

CURRENT_DIR = Path(__file__).resolve().parent
for candidate in (CURRENT_DIR, *CURRENT_DIR.parents):
    if (candidate / "core").exists():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        break

from core.plugin.entities.plugin import PluginDeclaration

DEFAULT_PACKAGE = CURRENT_DIR / "dist" / "model-hub-provider-0.1.5.difypkg"


def inspect_package(path: Path) -> dict:
    with zipfile.ZipFile(path, "r") as archive:
        names = sorted(archive.namelist())
        manifest = yaml.safe_load(archive.read("manifest.yaml").decode("utf-8"))

    declaration = PluginDeclaration.model_validate(manifest)
    return {
        "package": str(path),
        "entry_total": len(names),
        "entries": names,
        "manifest": {
            "author": declaration.author,
            "name": declaration.name,
            "category": declaration.category.value,
            "provider": declaration.model.provider if declaration.model else "",
        },
    }


def main() -> None:
    result = inspect_package(DEFAULT_PACKAGE)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
