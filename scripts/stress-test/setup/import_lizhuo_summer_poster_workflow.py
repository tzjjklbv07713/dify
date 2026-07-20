#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from pathlib import Path

import httpx

sys.path.append(str(Path(__file__).parent.parent))

from common import Logger, config_helper  # type: ignore[import]

DSL_FILENAME = "lizhuo_summer_poster_workflow.yml"
APP_NAME = "lizhuo_summer_poster_workflow"
BASE_URL = "http://localhost:5001"


def is_successful_import_response(response_data: dict[str, object]) -> bool:
    return response_data.get("status") != "failed" and bool(response_data.get("app_id"))


def build_headers() -> dict[str, str]:
    return {
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "DNT": "1",
        "Origin": "http://localhost:3000",
        "Pragma": "no-cache",
        "Referer": "http://localhost:3000/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        **config_helper.console_auth_headers(),
        "content-type": "application/json",
        "sec-ch-ua": '"Not;A=Brand";v="99", "Google Chrome";v="139", "Chromium";v="139"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }


def import_workflow_app() -> bool:
    log = Logger("ImportLizhuoWorkflow")
    log.header("Importing Lizhuo Summer Poster Workflow")

    access_token = config_helper.get_token()
    if not access_token:
        log.error("No access token found in config")
        log.info("Please run login_admin.py first to get access token")
        return False

    dsl_path = Path(__file__).parent / "dsl" / DSL_FILENAME
    if not dsl_path.exists():
        log.error(f"DSL file not found: {dsl_path}")
        return False

    yaml_content = dsl_path.read_text(encoding="utf-8")
    import_payload = {"mode": "yaml-content", "yaml_content": yaml_content}
    import_endpoint = f"{BASE_URL}/console/api/apps/imports"

    log.step("Importing workflow app from DSL...")
    log.key_value("DSL file", dsl_path.name)
    log.key_value("App name", APP_NAME)

    try:
        with httpx.Client() as client:
            response = client.post(
                import_endpoint,
                json=import_payload,
                headers=build_headers(),
                cookies=config_helper.console_auth_cookies(),
            )

        if response.status_code == 200:
            response_data = response.json()
            if is_successful_import_response(response_data):
                app_id = response_data.get("app_id")
                if response_data.get("status") != "completed":
                    log.warning(f"Import status: {response_data.get('status')}")
                    log.debug(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")

                log.success("Workflow app imported successfully!")
                log.key_value("App ID", app_id)
                log.key_value("App Mode", response_data.get("app_mode"))
                log.key_value("DSL Version", response_data.get("imported_dsl_version"))

                app_config = {
                    "app_id": app_id,
                    "app_mode": response_data.get("app_mode"),
                    "app_name": APP_NAME,
                    "dsl_version": response_data.get("imported_dsl_version"),
                    "dsl_file": DSL_FILENAME,
                }
                if config_helper.write_config("app_config", app_config):
                    log.info(f"App config saved to: {config_helper.get_config_path('benchmark_state')}")
                    return True
                return False

            if response_data.get("status") == "failed":
                log.error("Import failed")
                log.error(f"Error: {response_data.get('error')}")
                return False

            log.error("Import response did not include app_id")
            log.debug(f"Response: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return False

        if response.status_code == 401:
            log.error("Import failed: Unauthorized")
            log.info("Token may have expired. Please run login_admin.py again")
            return False

        log.error(f"Import failed with status code: {response.status_code}")
        log.debug(f"Response: {response.text}")
        return False
    except httpx.ConnectError:
        log.error(f"Could not connect to Dify API at {BASE_URL}")
        log.info("Make sure the API server is running with the local dev stack")
        return False
    except Exception as exc:
        log.error(f"An error occurred: {exc}")
        return False


if __name__ == "__main__":
    if not import_workflow_app():
        sys.exit(1)
