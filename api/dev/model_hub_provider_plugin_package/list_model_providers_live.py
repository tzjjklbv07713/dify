# ruff: noqa: T201

"""List model providers visible to the current tenant."""

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
from models.account import Account
from services.account_service import TenantService
from services.model_provider_service import ModelProviderService

EMAIL = "admin@bblizhuo.local"


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        providers = ModelProviderService().get_provider_list(tenant_id)
        payload = [
            {
                "provider": item.provider,
                "label": item.label.model_dump() if item.label else None,
                "preferred_provider_type": item.preferred_provider_type.value,
                "supported_model_types": [model_type.value for model_type in item.supported_model_types],
                "status": item.custom_configuration.status.value,
                "current_credential_name": item.custom_configuration.current_credential_name,
            }
            for item in providers
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
