#!/usr/bin/env python3
"""Fail when a critical dataset case is missing, errored, or below threshold."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_dataset(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number} must contain a JSON object")
            rows.append(value)
    return rows


def is_critical(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def numeric_threshold(value: Any, default: float) -> float:
    match = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(match.group()) if match else default


def thresholds(results: dict[str, Any], default: float) -> dict[str, float]:
    values: dict[str, float] = {}
    for item in results.get("thresholds", []):
        if isinstance(item, dict) and item.get("metric"):
            values[str(item["metric"]).lower()] = numeric_threshold(
                item.get("expected"), default
            )
    return values


def find_result(
    case: dict[str, Any], result_rows: list[dict[str, Any]]
) -> dict[str, Any] | None:
    case_id = str(case.get("id", ""))
    case_input = str(case.get("input", ""))
    for row in result_rows:
        row_ids = (row.get("id"), row.get("case_id"), row.get("dataset_id"))
        if case_id and case_id in {str(value) for value in row_ids if value is not None}:
            return row
        if case_input and str(row.get("input", "")) == case_input:
            return row
    return None


def evaluate(
    dataset: list[dict[str, Any]], results: dict[str, Any], default: float
) -> dict[str, Any]:
    critical = [case for case in dataset if is_critical(case.get("critical"))]
    result_rows = [row for row in results.get("rows", []) if isinstance(row, dict)]
    minimums = thresholds(results, default)
    findings = []

    for case in critical:
        case_id = str(case.get("id", "<missing-id>"))
        row = find_result(case, result_rows)
        failures = []
        scores: dict[str, float] = {}
        if row is None:
            failures.append("result row is missing")
        else:
            if row.get("error"):
                failures.append(f"execution error: {row['error']}")
            metrics = [item for item in row.get("metrics", []) if isinstance(item, dict)]
            if not metrics:
                failures.append("evaluator metrics are missing")
            for metric in metrics:
                name = str(metric.get("name", "<unnamed>")).lower()
                if metric.get("error"):
                    failures.append(f"{name} scorer error: {metric['error']}")
                    continue
                try:
                    score = float(metric["value"])
                except (KeyError, TypeError, ValueError):
                    failures.append(f"{name} score is missing or nonnumeric")
                    continue
                scores[name] = score
                minimum = minimums.get(name, default)
                if score < minimum:
                    failures.append(f"{name} score {score:g} is below {minimum:g}")
            for name in sorted(set(minimums) - set(scores)):
                failures.append(f"{name} evaluator result is missing")
        findings.append(
            {"id": case_id, "passed": not failures, "scores": scores, "failures": failures}
        )

    if not critical:
        findings.append(
            {
                "id": "<dataset>",
                "passed": False,
                "scores": {},
                "failures": ["dataset has no critical cases"],
            }
        )
    return {
        "version": 1,
        "passed": bool(critical) and all(item["passed"] for item in findings),
        "critical_cases": findings,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--default-minimum", type=float, default=3.0)
    args = parser.parse_args()

    try:
        report = evaluate(
            load_dataset(args.dataset), load_json(args.results), args.default_minimum
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Critical-case gate error: {error}", file=sys.stderr)
        return 1

    for item in report["critical_cases"]:
        state = "PASS" if item["passed"] else "FAIL"
        detail = "; ".join(item["failures"]) or "all evaluator scores passed"
        print(f"{state} {item['id']}: {detail}")
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
