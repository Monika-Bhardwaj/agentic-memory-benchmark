"""Counterfactual consistency measurement.

Measures whether controlled changes in memory state produce predictable
changes in downstream behavior.
"""

from __future__ import annotations

from typing import Any


def counterfactual_consistency_rate(
    paired_outcomes: list[dict],
) -> dict:
    """Compute the Counterfactual Consistency Rate (CCR).

    CCR = P(answer changes in predicted direction | memory state changed)

    Args:
        paired_outcomes: List of paired outcome dicts, each containing:
            - condition_a: outcome under memory state A
            - condition_b: outcome under memory state B
            - expected_direction: "A" or "B" (which condition should produce
              the correct answer)

    Returns:
        dict with CCR and related statistics.
    """
    if not paired_outcomes:
        return {"ccr": None, "n_pairs": 0, "n_consistent": 0}

    n_consistent = 0
    n_total = len(paired_outcomes)

    for pair in paired_outcomes:
        outcome_a = pair.get("condition_a", {})
        outcome_b = pair.get("condition_b", {})
        expected = pair.get("expected_direction", "A")

        # Check if the answer changed in the predicted direction
        answer_a = outcome_a.get("answer", "")
        answer_b = outcome_b.get("answer", "")

        if expected == "A":
            # Condition A should be correct, B should be wrong
            consistent = outcome_a.get("success", False) and not outcome_b.get("success", True)
        else:
            # Condition B should be correct, A should be wrong
            consistent = outcome_b.get("success", False) and not outcome_a.get("success", True)

        if consistent:
            n_consistent += 1

    ccr = n_consistent / n_total if n_total > 0 else 0.0

    return {
        "ccr": ccr,
        "n_pairs": n_total,
        "n_consistent": n_consistent,
        "interpretation": _interpret_ccr(ccr),
    }


def _interpret_ccr(ccr: float) -> str:
    """Interpret the CCR value."""
    if ccr >= 0.9:
        return "Strong causal memory effect"
    elif ccr >= 0.7:
        return "Moderate causal memory effect"
    elif ccr >= 0.5:
        return "Weak causal memory effect"
    elif ccr >= 0.3:
        return "Minimal causal memory effect"
    else:
        return "No detectable causal memory effect"


def paired_comparison(
    outcome_a: dict,
    outcome_b: dict,
    expected_direction: str = "A",
) -> dict:
    """Compare a single pair of counterfactual outcomes.

    Returns:
        dict with comparison results.
    """
    answer_a = outcome_a.get("answer", "")
    answer_b = outcome_b.get("answer", "")
    success_a = outcome_a.get("success", False)
    success_b = outcome_b.get("success", False)

    if expected_direction == "A":
        consistent = success_a and not success_b
    else:
        consistent = success_b and not success_a

    return {
        "answer_a": answer_a,
        "answer_b": answer_b,
        "success_a": success_a,
        "success_b": success_b,
        "expected_direction": expected_direction,
        "consistent": consistent,
        "answer_changed": answer_a != answer_b,
    }
