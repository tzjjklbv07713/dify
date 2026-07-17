# ruff: noqa: T201

"""Uninstall the current model-hub plugin installation by installation_id."""

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
from core.plugin.plugin_service import PluginService
from extensions.ext_database import db
from models.account import Account
from services.account_service import TenantService

EMAIL = "admin@bblizhuo.local"
INSTALLATION_ID = "019f3a01-6b8c-7b80-917c-92a0a143beed"


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        result = PluginService.uninstall(tenant_id, INSTALLATION_ID)
        print(
            json.dumps(
                {
                    "tenant_id": tenant_id,
                    "installation_id": INSTALLATION_ID,
                    "success": result,
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
