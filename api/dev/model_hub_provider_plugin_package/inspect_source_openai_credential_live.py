# ruff: noqa: T201

"""Inspect the current OpenAI-compatible relay credential without leaking full secrets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

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
SOURCE_PROVIDER = "langgenius/openai/openai"


def _short(value: str | None) -> dict[str, str | int | None]:
    text = value or ""
    return {
        "len": len(text),
        "prefix": text[:6],
        "suffix": text[-4:] if text else "",
    }


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        service = ModelProviderService()
        creds = service.get_provider_credential(tenant_id, SOURCE_PROVIDER, None)
        if not creds:
            raise RuntimeError("source_provider_credentials_not_found")

        base = str(creds.get("openai_api_base") or "").rstrip("/")
        key = str(creds.get("openai_api_key") or "")

        endpoint_checks: list[dict[str, object]] = []
        for path in ("/v1/models", "/models"):
            url = f"{base}{path}"
            try:
                response = requests.get(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=(10, 30),
                )
                endpoint_checks.append(
                    {
                        "path": path,
                        "status_code": response.status_code,
                        "body_prefix": response.text[:200],
                    }
                )
            except Exception as exc:
                endpoint_checks.append(
                    {
                        "path": path,
                        "error": str(exc),
                    }
                )

        print(
            json.dumps(
                {
                    "provider": SOURCE_PROVIDER,
                    "base": base,
                    "api_protocol": creds.get("api_protocol"),
                    "validate_model": creds.get("validate_model"),
                    "api_key": _short(key),
                    "endpoint_checks": endpoint_checks,
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
