# ruff: noqa: T201

"""Poll a plugin installation task until it reaches a terminal status."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
for candidate in (CURRENT_DIR, *CURRENT_DIR.parents):
    if (candidate / "core").exists():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        break

from app import app
from core.plugin.plugin_service import PluginService
from extensions.ext_database import db
from models.account import Account
from services.account_service import TenantService

EMAIL = "admin@bblizhuo.local"
TASK_ID = "019f39f8-e0c7-7268-8c26-3003dd64a809"
MAX_POLLS = 20
SLEEP_SECONDS = 3


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)

        last_payload = None
        for _ in range(MAX_POLLS):
            task = PluginService.fetch_install_task(tenant_id, TASK_ID)
            last_payload = {
                "task_id": task.id,
                "status": task.status.value,
                "total_plugins": task.total_plugins,
                "completed_plugins": task.completed_plugins,
                "plugins": [
                    {
                        "plugin_unique_identifier": item.plugin_unique_identifier,
                        "plugin_id": item.plugin_id,
                        "status": item.status.value,
                        "message": item.message,
                    }
                    for item in task.plugins
                ],
            }
            if task.status.value in {"success", "failed"}:
                print(json.dumps(last_payload, ensure_ascii=False, indent=2))
                return
            time.sleep(SLEEP_SECONDS)

        print(json.dumps(last_payload or {"task_id": TASK_ID, "status": "unknown"}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
