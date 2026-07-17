# ruff: noqa: T201

"""Inspect app model config bindings for current Dify apps."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
for candidate in (CURRENT_DIR, *CURRENT_DIR.parents):
    if (candidate / "core").exists():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        break

from app import app
from extensions.ext_database import db
from models.model import App


def _parse_json(text: str | None):
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        return text


def main() -> None:
    with app.app_context():
        apps = db.session.query(App).all()
        payload = []
        for app_model in apps:
            config = app_model.app_model_config
            payload.append(
                {
                    "id": app_model.id,
                    "name": app_model.name,
                    "mode": app_model.mode.value if hasattr(app_model.mode, "value") else str(app_model.mode),
                    "status": app_model.status,
                    "app_model_config_id": app_model.app_model_config_id,
                    "model": _parse_json(config.model) if config else None,
                }
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
