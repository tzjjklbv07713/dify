# ruff: noqa: T201

"""Invoke the current default tenant LLM once and print a concise result."""

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
from core.model_manager import ModelManager
from extensions.ext_database import db
from graphon.model_runtime.entities.message_entities import UserPromptMessage
from graphon.model_runtime.entities.model_entities import ModelType
from models.account import Account
from services.account_service import TenantService

EMAIL = "admin@bblizhuo.local"
PROMPT = "请只回复 OK"


def _extract_text(result) -> str:
    message = getattr(result, "message", None)
    if message is None:
        return ""
    getter = getattr(message, "get_text_content", None)
    if callable(getter):
        return str(getter() or "").strip()
    return str(getattr(message, "content", "") or "").strip()


def main() -> None:
    with app.app_context():
        account = db.session.query(Account).filter(Account.email == EMAIL).first()
        if not account:
            raise RuntimeError("account_not_found")
        tenant_id = str(TenantService.get_join_tenants(account, session=db.session)[0].id)
        instance = ModelManager.for_tenant(tenant_id=tenant_id).get_default_model_instance(
            tenant_id=tenant_id,
            model_type=ModelType.LLM,
        )
        result = instance.invoke_llm(
            prompt_messages=[UserPromptMessage(content=PROMPT)],
            model_parameters={"temperature": 0},
            stream=False,
        )
        print(
            json.dumps(
                {
                    "provider": instance.provider,
                    "model": instance.model_name,
                    "reply": _extract_text(result),
                },
                ensure_ascii=False,
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
