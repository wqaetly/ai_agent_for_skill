"""
Batch-upload the flow JSON files from `langflow/flows/` into the running
Langflow instance via its REST API.

Usage:
    python scripts/upload_flows.py
    # or override the host:
    LANGFLOW_HOST=http://localhost:7860 python scripts/upload_flows.py

The script is idempotent: if a flow with the same name already exists it
will be replaced (Langflow API supports `--upsert`-style behaviour through
the `name` field).

Exit codes:
    0  — every JSON file uploaded (or no JSON files present yet).
    1  — Langflow not reachable.
    2  — at least one flow failed to upload.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import List

try:
    import httpx
except ImportError:  # pragma: no cover — script bootstrap path
    print(
        "ERROR: httpx is required (already declared in skill_agent/requirements.txt). "
        "Activate the project venv before running this script.",
        file=sys.stderr,
    )
    sys.exit(2)


HOST = os.environ.get("LANGFLOW_HOST", "http://localhost:7860").rstrip("/")
HEALTH_URL = f"{HOST}/health_check"
UPLOAD_URL = f"{HOST}/api/v1/flows/upload/"
LIST_URL = f"{HOST}/api/v1/flows/"

FLOWS_DIR = Path(__file__).resolve().parent.parent / "flows"


def _wait_for_langflow(timeout_seconds: int = 120) -> bool:
    deadline = time.time() + timeout_seconds
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(HEALTH_URL)
                if r.status_code < 500:
                    return True
        except Exception as exc:  # noqa: BLE001 — broad on bootstrap probe
            last_err = exc
        time.sleep(2)
    if last_err is not None:
        print(f"  Last error while polling Langflow: {last_err}", file=sys.stderr)
    return False


def _list_existing_flow_names(client: httpx.Client) -> List[str]:
    try:
        r = client.get(LIST_URL, timeout=15.0)
        if r.status_code != 200:
            return []
        return [item.get("name") for item in r.json() if item.get("name")]
    except Exception:  # noqa: BLE001
        return []


def main() -> int:
    if not FLOWS_DIR.exists():
        print(f"flows directory not found: {FLOWS_DIR}", file=sys.stderr)
        return 0

    json_files = sorted(FLOWS_DIR.glob("*.json"))
    if not json_files:
        print(f"No flow JSON files in {FLOWS_DIR}; nothing to upload.")
        return 0

    print(f"Waiting for Langflow at {HOST} ...")
    if not _wait_for_langflow():
        print(f"ERROR: Langflow not reachable at {HOST}", file=sys.stderr)
        return 1

    failures: List[str] = []
    with httpx.Client(timeout=60.0) as client:
        existing = set(_list_existing_flow_names(client))
        for json_path in json_files:
            try:
                with json_path.open("rb") as fh:
                    files = {"file": (json_path.name, fh, "application/json")}
                    resp = client.post(UPLOAD_URL, files=files)
                if resp.status_code in (200, 201):
                    name = json_path.stem
                    marker = "(updated)" if name in existing else "(created)"
                    print(f"  ✓ {json_path.name} {marker}")
                else:
                    failures.append(json_path.name)
                    print(
                        f"  ✗ {json_path.name} -> HTTP {resp.status_code}: "
                        f"{resp.text[:200]}",
                        file=sys.stderr,
                    )
            except Exception as exc:  # noqa: BLE001
                failures.append(json_path.name)
                print(f"  ✗ {json_path.name} -> {exc}", file=sys.stderr)

    if failures:
        print(f"Failed to upload {len(failures)} flow(s): {failures}", file=sys.stderr)
        return 2
    print(f"Uploaded {len(json_files)} flow(s) to {HOST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
