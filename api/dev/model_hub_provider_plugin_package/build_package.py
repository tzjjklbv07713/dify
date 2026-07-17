# ruff: noqa: T201

"""Build a daemon-compatible `.difypkg` archive for the model-hub provider."""

from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

import yaml

CURRENT_DIR = Path(__file__).resolve().parent
API_ROOT = CURRENT_DIR.parents[1]
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))

from core.plugin.entities.plugin import PluginDeclaration

PACKAGE_DIR = CURRENT_DIR
DEFAULT_OUTPUT = PACKAGE_DIR / "dist" / "model-hub-provider-0.1.5.difypkg"


def validate_manifest(manifest_path: Path) -> dict:
    if manifest_path.suffix in {".yaml", ".yml"}:
        manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    PluginDeclaration.model_validate(manifest)
    return manifest


def build_package(*, output_path: Path = DEFAULT_OUTPUT) -> Path:
    manifest_path = PACKAGE_DIR / "manifest.yaml"
    validate_manifest(manifest_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    include_roots = [
        "manifest.yaml",
        "README.md",
        "main.py",
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        ".difyignore",
        "_assets",
        "provider",
        "models",
    ]

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for include_root in include_roots:
            path = PACKAGE_DIR / include_root
            if path.is_file():
                archive.write(path, arcname=path.relative_to(PACKAGE_DIR))
                continue

            for child in sorted(path.rglob("*")):
                if child.is_dir():
                    continue
                if "__pycache__" in child.parts:
                    continue
                if child.suffix == ".pyc":
                    continue
                if child.name == "manifest.json":
                    continue
                archive.write(child, arcname=child.relative_to(PACKAGE_DIR))

    return output_path


def main() -> None:
    output_path = build_package()
    print(output_path)


if __name__ == "__main__":
    main()
