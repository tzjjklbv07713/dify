# ruff: noqa: T201

"""Run the local package verification chain for the model-hub provider."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
API_ROOT = CURRENT_DIR.parents[1]


def _run(args: list[str]) -> dict[str, object]:
    completed = subprocess.run(
        args,
        cwd=API_ROOT.parent,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "args": args,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> None:
    results = [
        _run([sys.executable, "-m", "py_compile", str(CURRENT_DIR / "build_package.py")]),
        _run(["uv", "run", "--project", "api", "python", str(CURRENT_DIR / "build_package.py")]),
        _run(["uv", "run", "--project", "api", "python", str(CURRENT_DIR / "inspect_package.py")]),
    ]
    print(json.dumps(results, ensure_ascii=True, indent=2))
    if any(item["returncode"] != 0 for item in results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
