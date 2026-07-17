# ruff: noqa: T201

"""Decode a local package, then install it by the returned unique identifier."""

from __future__ import annotations

import json
import os
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

EMAIL = os.environ.get("MODEL_HUB_INSTALL_EMAIL", "admin@bblizhuo.local")
PACKAGE_PATH = Path(os.environ.get("MODEL_HUB_PACKAGE_PATH", "/app/api/model-hub-provider-0.1.5.difypkg"))


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        decode = PluginService.upload_pkg(
            tenant_id,
            PACKAGE_PATH.read_bytes(),
            verify_signature=False,
        )
        install = PluginService.install_from_local_pkg(tenant_id, [decode.unique_identifier])
        print(
            json.dumps(
                {
                    "tenant_id": tenant_id,
                    "unique_identifier": decode.unique_identifier,
                    "all_installed": install.all_installed,
                    "task_id": install.task_id,
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
