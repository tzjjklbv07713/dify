# ruff: noqa: T201

"""List current tenant plugins to verify installation presence."""

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
from core.plugin.impl.plugin import PluginInstaller
from extensions.ext_database import db
from models.account import Account
from services.account_service import TenantService

EMAIL = "admin@bblizhuo.local"


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        plugins = PluginInstaller().list_plugins(tenant_id)
        payload = [
            {
                "plugin_id": item.plugin_id,
                "plugin_unique_identifier": item.plugin_unique_identifier,
                "installation_id": item.installation_id,
            }
            for item in plugins
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
