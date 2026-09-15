"""Frozen deterministic success predicate.

Exactly as specified in ``benchmark/v0/SPEC.md`` §3.2:
truthy iff every ``values`` string is a substring of the normalized answer and no
``forbid`` string is. Normalization ``lower_strip``: lowercase, strip surrounding
whitespace, collapse runs of whitespace.
"""

from __future__ import annotations

import re


def normalize_answer(text: str, mode: str = "lower_strip") -> str:
    if mode == "none":
        return text
    if mode == "lower_strip":
        return re.sub(r"\s+", " ", text.strip().lower())
    raise ValueError(f"unknown normalization: {mode}")


def apply_success_criterion(criterion: dict, answer: str | None) -> tuple[bool, dict]:
    """Returns (success, detail). A ``None``/empty answer is scored False by design
    (no fabrications or forgiving of empty output)."""
    if answer is None:
        return False, {"reason": "no_answer"}
    mode = criterion.get("normalization", "lower_strip")
    norm_answer = normalize_answer(answer, mode)
    values = [normalize_answer(v, mode) for v in criterion.get("values", [])]
    forbid = [normalize_answer(v, mode) for v in criterion.get("forbid", [])]

    missing = [v for v in values if v and v not in norm_answer]
    present_forbidden = [v for v in forbid if v and v in norm_answer]
    success = (not missing) and (not present_forbidden)
    return success, {
        "norm_answer": norm_answer,
        "missing_required": missing,
        "forbidden_present": present_forbidden,
        "reason": None if success else ("missing_required" if missing else "forbidden_present"),
    }