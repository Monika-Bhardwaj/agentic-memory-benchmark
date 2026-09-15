"""Schema validation and custom task invariants.

Two layers:
1. JSON-Schema conformance to ``benchmark/v0/schema.json`` (enforced).
2. Custom semantic invariants (event-id uniqueness, query/event agreement, directive
   targets existing in the stream, update/payload id consistency).
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "benchmark" / "v0" / "schema.json"

_SCHEMA_CACHE: Draft202012Validator | None = None


def get_validator() -> Draft202012Validator:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as fh:
            schema = json.load(fh)
        _SCHEMA_CACHE = Draft202012Validator(schema)
    return _SCHEMA_CACHE


def schema_errors(task: dict) -> list[str]:
    validator = get_validator()
    errors = sorted((e.message for e in validator.iter_errors(task)))
    return errors


def semantic_errors(task: dict) -> list[str]:
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

    tracked: set[str] = set()
    for e in events:
        kind = e["kind"]
        if kind == "user_message" and e.get("item"):
            tracked.add(e["item"]["item_id"])
        elif kind == "memory_update":
            target, payload = e.get("item_id"), e.get("item", {}).get("item_id")
            if target is None or payload is None:
                issues.append(f"memory_update {e['event_id']} missing item_id/item")
            elif target != payload:
                issues.append(f"memory_update {e['event_id']} target != payload item_id")
            if target not in tracked:
                issues.append(f"memory_update {e['event_id']} targets unknown item {target}")
            tracked.add(target)
        elif kind == "memory_forget":
            target = e.get("item_id")
            if target is None:
                issues.append(f"memory_forget {e['event_id']} missing item_id")
            elif target not in tracked:
                issues.append(f"memory_forget {e['event_id']} targets unknown item {target}")
            tracked.discard(target)

    for rid in task.get("required_item_ids", []):
        if rid and rid not in tracked and not any(e.get("item", {}).get("item_id") == rid for e in events):
            issues.append(f"required_item_id {rid} never appears in the stream")

    for did in task.get("distractor_event_ids", []):
        if did not in ids:
            issues.append(f"distractor_event_ids references unknown {did}")

    return issues


def validate_task(task: dict) -> list[str]:
    return schema_errors(task) + semantic_errors(task)


def is_valid(task: dict) -> bool:
    return not validate_task(task)