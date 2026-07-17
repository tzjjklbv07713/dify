# ruff: noqa: T201

"""Inspect model-hub provider model status and current default LLM."""

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
TARGET_PROVIDER = "your-company/model-hub-provider/model_hub"


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        svc = ModelProviderService()
        models = svc.get_models_by_provider(tenant_id, TARGET_PROVIDER)
        default_model = svc.get_default_model_of_model_type(tenant_id, "llm")
        print(
            json.dumps(
                {
                    "provider": TARGET_PROVIDER,
                    "models": [
                        {
                            "model": item.model,
                            "model_type": item.model_type.value,
                            "status": item.status.value if item.status else None,
                            "fetch_from": item.fetch_from.value,
                        }
                        for item in models
                    ],
                    "default_llm": {
                        "model": default_model.model if default_model else None,
                        "provider": default_model.provider.provider if default_model else None,
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
