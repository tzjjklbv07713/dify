# ruff: noqa: T201

"""Live smoke script for the model-hub provider runtime scaffold.

This helper is intentionally outside the future plugin package runtime. It lets
us exercise the real proxy before the final plugin-daemon packaging is wired.

Usage examples:

1. Run against explicit proxy credentials:
   python smoke_live.py --base-url https://proxy.example.com --api-key sk-xxx --model gpt-5.5

2. Reuse the current Dify OpenAI-compatible provider credential:
   python smoke_live.py --from-dify-openai-provider --model gpt-5.5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CURRENT_DIR = Path(__file__).resolve().parent
for candidate in (CURRENT_DIR, *CURRENT_DIR.parents):
    if (candidate / "core").exists():
        if str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))
        break

from app import app
from dev.model_hub_provider_plugin_package.src.model_hub_provider.provider_runtime import ModelHubProviderRuntime
from extensions.ext_database import db
from graphon.model_runtime.entities.message_entities import SystemPromptMessage, UserPromptMessage
from models.account import Account
from services.account_service import TenantService
from services.model_provider_service import ModelProviderService


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Live smoke test for the model-hub provider scaffold.")
    parser.add_argument("--base-url", dest="base_url", default="", help="Proxy base URL")
    parser.add_argument("--api-key", dest="api_key", default="", help="Proxy API key")
    parser.add_argument("--catalog-path", dest="catalog_path", default="/provider/models")
    parser.add_argument("--api-protocol", dest="api_protocol", default="responses")
    parser.add_argument("--model", dest="model", default="gpt-5.5")
    parser.add_argument("--message", dest="message", default="Please reply with OK only.")
    parser.add_argument("--from-dify-openai-provider", action="store_true")
    parser.add_argument("--provider-email", dest="provider_email", default="admin@bblizhuo.local")
    return parser.parse_args()


def _load_from_dify_openai_provider(email: str) -> dict[str, Any]:
    account = db.session.query(Account).filter(Account.email == email).first()
    if not account:
        raise RuntimeError("account_not_found")
    tenants = TenantService.get_join_tenants(account, session=db.session)
    if not tenants:
        raise RuntimeError("tenant_not_found")
    tenant_id = str(tenants[0].id)
    credentials = ModelProviderService().get_provider_credential(
        tenant_id=tenant_id,
        provider="langgenius/openai/openai",
    )
    if not credentials:
        raise RuntimeError("openai_provider_credentials_missing")
    return {
        "proxy_base_url": credentials["openai_api_base"],
        "proxy_api_key": credentials["openai_api_key"],
        "catalog_path": "/provider/models",
        "api_protocol": credentials.get("api_protocol") or "responses",
    }


def run_smoke(*, credentials: dict[str, Any], model: str, message: str) -> dict[str, Any]:
    runtime = ModelHubProviderRuntime(credentials=credentials)
    provider_ping = runtime.validate_provider_credentials()
    models = runtime.fetch_remote_models()
    result = runtime.invoke_llm(
        model=model,
        prompt_messages=[
            SystemPromptMessage(content="You are a concise assistant."),
            UserPromptMessage(content=message),
        ],
        stream=False,
    )
    return {
        "provider_ping": provider_ping,
        "catalog_total": len(models),
        "catalog_sample": [item.model for item in models[:20]],
        "reply_model": result.model,
        "reply_text": result.message.content,
        "usage_total_tokens": result.usage.total_tokens,
    }


def main() -> None:
    args = _parse_args()
    with app.app_context():
        if args.from_dify_openai_provider:
            credentials = _load_from_dify_openai_provider(args.provider_email)
        else:
            if not args.base_url or not args.api_key:
                raise RuntimeError("base_url_and_api_key_required")
            credentials = {
                "proxy_base_url": args.base_url,
                "proxy_api_key": args.api_key,
                "catalog_path": args.catalog_path,
                "api_protocol": args.api_protocol,
            }

        result = run_smoke(
            credentials=credentials,
            model=args.model,
            message=args.message,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
