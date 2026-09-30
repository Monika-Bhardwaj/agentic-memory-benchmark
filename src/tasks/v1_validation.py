"""Schema validation for benchmark v1 tasks.

Validates against the v1 schema (benchmark/v1/schema.json) with multimodal
and intervention support.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
V1_SCHEMA_PATH = ROOT / "benchmark" / "v1" / "schema.json"

_SCHEMA_CACHE: Draft202012Validator | None = None


def get_v1_validator() -> Draft202012Validator:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(V1_SCHEMA_PATH, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
        _SCHEMA_CACHE = Draft202012Validator(schema)
    return _SCHEMA_CACHE


def v1_schema_errors(task: dict) -> list[str]:
    validator = get_v1_validator()
    errors = sorted((e.message for e in validator.iter_errors(task)))
    return errors


def v1_semantic_errors(task: dict) -> list[str]:
    """Custom invariants beyond the JSON schema."""
    issues: list[str] = []
    events = task.get("events", [])

    ids = [e["event_id"] for e in events]
    if len(ids) != len(set(ids)):
        issues.append("duplicate event_id")

    if not events or events[-1]["kind"] != "query":
        issues.append("last event must be a query")
    elif task.get("query") != events[-1].get("text"):
        issues.append("task.query must equal final query event text")

    # Check required_item_ids appear in stream
    for rid in task.get("required_item_ids", []):
        if rid and not any(e.get("item", {}).get("item_id") == rid for e in events):
            issues.append(f"required_item_id {rid} never appears in the stream")

    # Check intervention is present
    if "intervention" not in task:
        issues.append("missing intervention field")

    return issues


def validate_v1_task(task: dict) -> list[str]:
    return v1_schema_errors(task) + v1_semantic_errors(task)


def is_valid_v1(task: dict) -> bool:
    return not validate_v1_task(task)
