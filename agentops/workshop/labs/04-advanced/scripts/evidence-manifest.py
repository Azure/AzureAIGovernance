#!/usr/bin/env python3
"""Write a compact manifest that links release evidence to immutable inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def digest(path: Path) -> str | None:
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--cloud-run", type=Path, required=True)
    parser.add_argument("--smoke-log", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    results = read_json(args.results)
    cloud = read_json(args.cloud_run)
    manifest = {
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_run_url": os.getenv("PIPELINE_RUN_URL", ""),
        "source_commit": os.getenv("SOURCE_COMMIT", ""),
        "test_agent": os.getenv("TEST_AGENT", ""),
        "test_agent_version": os.getenv("TEST_AGENT_VERSION", ""),
        "foundry_evaluation": {
            key: cloud.get(key, "") for key in ("status", "eval_id", "run_id", "report_url")
        },
        "evaluators": results.get("evaluators", []),
        "files": {
            "dataset": {"path": str(args.dataset), "sha256": digest(args.dataset)},
            "config": {"path": str(args.config), "sha256": digest(args.config)},
            "results": {"path": str(args.results), "sha256": digest(args.results)},
            "cloud_run": {"path": str(args.cloud_run), "sha256": digest(args.cloud_run)},
            "smoke_log": {"path": str(args.smoke_log), "sha256": digest(args.smoke_log)},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
