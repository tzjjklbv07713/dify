# ruff: noqa: T201

"""Clone the current OpenAI-compatible relay credential into model-hub provider."""

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
from core.plugin.impl.model_runtime_factory import create_plugin_provider_manager
from extensions.ext_database import db
from graphon.model_runtime.entities.model_entities import ModelType
from models.account import Account
from services.account_service import TenantService
from services.model_provider_service import ModelProviderService

EMAIL = "admin@bblizhuo.local"
SOURCE_PROVIDER = "langgenius/openai/openai"
TARGET_PROVIDER = "your-company/model-hub-provider/model_hub"
TARGET_CREDENTIAL_NAME = "立卓中转-ModelHub"


def _ensure_v1(url: str) -> str:
    clean = str(url or "").rstrip("/")
    if clean.endswith("/v1"):
        return clean
    return f"{clean}/v1" if clean else clean


def _target_variables(service: ModelProviderService, tenant_id: str) -> set[str]:
    providers = service.get_provider_list(tenant_id)
    target = next(item for item in providers if item.provider == TARGET_PROVIDER)
    schemas = target.provider_credential_schema.credential_form_schemas if target.provider_credential_schema else []
    return {schema.variable for schema in schemas}


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        service = ModelProviderService()
        variables = _target_variables(service, tenant_id)

        provider_configuration = (
            create_plugin_provider_manager(tenant_id=tenant_id).get_configurations(tenant_id).get(SOURCE_PROVIDER)
        )
        if not provider_configuration:
            raise RuntimeError("source_provider_configuration_not_found")
        source_credentials = provider_configuration.get_current_credentials(
            model_type=ModelType.LLM,
            model="gpt-5.4-mini",
        )
        if not source_credentials:
            raise RuntimeError("source_provider_credentials_not_found")

        endpoint_url = _ensure_v1(source_credentials.get("openai_api_base") or "")
        api_key = source_credentials.get("openai_api_key") or ""
        api_protocol = source_credentials.get("api_protocol") or "responses"
        validation_model = source_credentials.get("validate_model") or "gpt-5.4-mini"

        target_credentials: dict[str, str] = {}
        if "endpoint_url" in variables:
            target_credentials["endpoint_url"] = endpoint_url
        if "proxy_base_url" in variables:
            target_credentials["proxy_base_url"] = endpoint_url
        if "api_key" in variables:
            target_credentials["api_key"] = api_key
        if "proxy_api_key" in variables:
            target_credentials["proxy_api_key"] = api_key
        if "catalog_path" in variables:
            target_credentials["catalog_path"] = "/models"
        if "api_protocol" in variables:
            target_credentials["api_protocol"] = api_protocol
        if "validation_model" in variables:
            target_credentials["validation_model"] = validation_model
        if "validate_model" in variables:
            target_credentials["validate_model"] = validation_model
        if "timeout_ms" in variables:
            target_credentials["timeout_ms"] = "15000"
        if "mode" in variables:
            target_credentials["mode"] = "chat"

        service.validate_provider_credentials(tenant_id, TARGET_PROVIDER, target_credentials)
        available_credentials = service.get_provider_available_credentials(tenant_id, TARGET_PROVIDER, user=account)
        existing = next(
            (
                item
                for item in available_credentials
                if getattr(item, "credential_name", None) == TARGET_CREDENTIAL_NAME
            ),
            None,
        )
        if existing:
            service.update_provider_credential(
                tenant_id,
                TARGET_PROVIDER,
                target_credentials,
                existing.id,
                TARGET_CREDENTIAL_NAME,
            )
        else:
            service.create_provider_credential(
                tenant_id,
                TARGET_PROVIDER,
                target_credentials,
                TARGET_CREDENTIAL_NAME,
            )

        current = service.get_provider_list(tenant_id)
        target = next(item for item in current if item.provider == TARGET_PROVIDER)
        print(
            json.dumps(
                {
                    "target_provider": TARGET_PROVIDER,
                    "target_variables": sorted(variables),
                    "status": target.custom_configuration.status.value,
                    "current_credential_name": target.custom_configuration.current_credential_name,
                    "api_protocol": target_credentials.get("api_protocol"),
                    "endpoint_url": target_credentials.get("endpoint_url") or target_credentials.get("proxy_base_url"),
                    "validation_model": target_credentials.get("validation_model")
                    or target_credentials.get("validate_model"),
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
