# ruff: noqa: T201

"""Install or decode the local `.difypkg` through the running Dify backend.

This helper is meant for live environments where:

- the Dify API is already running
- plugin daemon is reachable from that API process
- we want to upload the locally-built `.difypkg` without going through the web UI
"""

from __future__ import annotations

import argparse
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

DEFAULT_PACKAGE = CURRENT_DIR / "dist" / "model-hub-provider-0.1.5.difypkg"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Install or decode the local model-hub `.difypkg`.")
    parser.add_argument("--email", default="admin@bblizhuo.local", help="Workspace account email")
    parser.add_argument("--package", default=str(DEFAULT_PACKAGE), help="Path to .difypkg")
    parser.add_argument("--verify-signature", action="store_true")
    parser.add_argument(
        "--mode",
        choices=["decode", "upload"],
        default="decode",
        help="decode only or upload through PluginService.upload_pkg",
    )
    return parser.parse_args()


def _resolve_tenant_id(email: str) -> str:
    account = db.session.query(Account).filter(Account.email == email).first()
    if not account:
        raise RuntimeError("account_not_found")
    tenants = TenantService.get_join_tenants(account, session=db.session)
    if not tenants:
        raise RuntimeError("tenant_not_found")
    return str(tenants[0].id)


def run_install(*, email: str, package_path: Path, verify_signature: bool, mode: str) -> dict:
    package_bytes = package_path.read_bytes()

    with app.app_context():
        tenant_id = _resolve_tenant_id(email)
        # Current Dify upload flow returns a decode response on upload, so both
        # modes intentionally share the same backend entrypoint for now.
        result = PluginService.upload_pkg(tenant_id, package_bytes, verify_signature=verify_signature)
        return {
            "tenant_id": tenant_id,
            "mode": mode,
            "package": str(package_path),
            "unique_identifier": result.unique_identifier,
            "manifest_name": result.manifest.name,
            "manifest_author": result.manifest.author,
        }


def main() -> None:
    args = _parse_args()
    package_path = Path(args.package)
    result = run_install(
        email=args.email,
        package_path=package_path,
        verify_signature=args.verify_signature,
        mode=args.mode,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
