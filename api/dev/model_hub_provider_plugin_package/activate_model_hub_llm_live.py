# ruff: noqa: T201

"""Create or update a custom LLM model credential for model-hub and make it default."""

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
MODEL_TYPE = "llm"
TARGET_CREDENTIAL_NAME = "立卓中转-ModelHub-LLM"


def _ensure_v1(url: str) -> str:
    clean = str(url or "").rstrip("/")
    if clean.endswith("/v1"):
        return clean
    return f"{clean}/v1" if clean else clean


def _build_target_credentials(source_credentials: dict, variables: set[str], model_name: str) -> dict[str, str]:
    endpoint_url = _ensure_v1(source_credentials.get("openai_api_base") or "")
    api_key = source_credentials.get("openai_api_key") or ""
    api_protocol = source_credentials.get("api_protocol") or "responses"
    validation_model = source_credentials.get("validate_model") or model_name

    payload: dict[str, str] = {}
    if "endpoint_url" in variables:
        payload["endpoint_url"] = endpoint_url
    if "proxy_base_url" in variables:
        payload["proxy_base_url"] = endpoint_url
    if "api_key" in variables:
        payload["api_key"] = api_key
    if "proxy_api_key" in variables:
        payload["proxy_api_key"] = api_key
    if "catalog_path" in variables:
        payload["catalog_path"] = "/models"
    if "api_protocol" in variables:
        payload["api_protocol"] = api_protocol
    if "validation_model" in variables:
        payload["validation_model"] = validation_model
    if "validate_model" in variables:
        payload["validate_model"] = validation_model
    if "timeout_ms" in variables:
        payload["timeout_ms"] = "15000"
    if "mode" in variables:
        payload["mode"] = "chat"
    if "context_size" in variables:
        payload["context_size"] = "128000"
    if "max_tokens_to_sample" in variables:
        payload["max_tokens_to_sample"] = "4096"
    if "function_calling_type" in variables:
        payload["function_calling_type"] = "tool_call"
    if "vision_support" in variables:
        payload["vision_support"] = "no_support"
    return payload


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        service = ModelProviderService()

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

        providers = service.get_provider_list(tenant_id)
        target_provider = next(item for item in providers if item.provider == TARGET_PROVIDER)
        variables = {
            schema.variable for schema in (target_provider.model_credential_schema.credential_form_schemas or [])
        }
        model_name = source_credentials.get("validate_model") or "gpt-5.4-mini"
        target_credentials = _build_target_credentials(source_credentials, variables, model_name)

        service.validate_model_credentials(
            tenant_id=tenant_id,
            provider=TARGET_PROVIDER,
            model_type=MODEL_TYPE,
            model=model_name,
            credentials=target_credentials,
        )

        available = service.get_provider_model_available_credentials(tenant_id, TARGET_PROVIDER, MODEL_TYPE, model_name)
        existing = next(
            (item for item in available if getattr(item, "credential_name", None) == TARGET_CREDENTIAL_NAME),
            None,
        )
        if existing:
            service.update_model_credential(
                tenant_id,
                TARGET_PROVIDER,
                MODEL_TYPE,
                model_name,
                target_credentials,
                existing.credential_id,
                TARGET_CREDENTIAL_NAME,
            )
            credential_id = existing.credential_id
        else:
            service.create_model_credential(
                tenant_id,
                TARGET_PROVIDER,
                MODEL_TYPE,
                model_name,
                target_credentials,
                TARGET_CREDENTIAL_NAME,
            )
            refreshed = service.get_provider_model_available_credentials(
                tenant_id, TARGET_PROVIDER, MODEL_TYPE, model_name
            )
            credential_id = next(
                item.credential_id
                for item in refreshed
                if getattr(item, "credential_name", None) == TARGET_CREDENTIAL_NAME
            )

        try:
            service.add_model_credential_to_model_list(
                tenant_id,
                TARGET_PROVIDER,
                MODEL_TYPE,
                model_name,
                credential_id,
            )
        except ValueError as exc:
            if "Can't add same credential" not in str(exc):
                raise
        service.switch_active_custom_model_credential(
            tenant_id,
            TARGET_PROVIDER,
            MODEL_TYPE,
            model_name,
            credential_id,
        )
        service.update_default_model_of_model_type(tenant_id, MODEL_TYPE, TARGET_PROVIDER, model_name)

        print(
            json.dumps(
                {
                    "provider": TARGET_PROVIDER,
                    "model_type": MODEL_TYPE,
                    "model_name": model_name,
                    "credential_id": credential_id,
                    "credential_name": TARGET_CREDENTIAL_NAME,
                    "variables": sorted(variables),
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
