"""Causal estimands for memory evaluation.

Pre-registered estimands that are identifiable from the benchmark design.
"""

from __future__ import annotations

import statistics
from typing import Any


def average_memory_effect(
    outcomes_with_memory: list[dict],
    outcomes_no_memory: list[dict],
) -> dict:
    """E1: Average memory effect.

    τ_memory = E[Y | memory] − E[Y | no memory]

    Identified by: random assignment of system (memory vs no-memory)
    holding task, model, budgets fixed.
    """
    if not outcomes_with_memory or not outcomes_no_memory:
        return {"estimand": "average_memory_effect", "value": None, "ci": None}

    mean_memory = sum(o["success"] for o in outcomes_with_memory) / len(outcomes_with_memory)
    mean_no_memory = sum(o["success"] for o in outcomes_no_memory) / len(outcomes_no_memory)
    effect = mean_memory - mean_no_memory

    return {
        "estimand": "average_memory_effect",
        "value": effect,
        "mean_memory": mean_memory,
        "mean_no_memory": mean_no_memory,
        "n_memory": len(outcomes_with_memory),
        "n_no_memory": len(outcomes_no_memory),
    }


def retrieval_effect(
    outcomes_retrieval: list[dict],
    outcomes_no_memory: list[dict],
) -> dict:
    """E2: Retrieval effect.

    τ_retrieval = E[Y | retrieval_only] − E[Y | no memory]
    """
    if not outcomes_retrieval or not outcomes_no_memory:
        return {"estimand": "retrieval_effect", "value": None}

    mean_retrieval = sum(o["success"] for o in outcomes_retrieval) / len(outcomes_retrieval)
    mean_no_memory = sum(o["success"] for o in outcomes_no_memory) / len(outcomes_no_memory)
    effect = mean_retrieval - mean_no_memory

    return {
        "estimand": "retrieval_effect",
        "value": effect,
        "mean_retrieval": mean_retrieval,
        "mean_no_memory": mean_no_memory,
    }


def memory_management_effect(
    outcomes_proposed: list[dict],
    outcomes_retrieval: list[dict],
) -> dict:
    """E3: Memory-management effect (central estimand).

    τ_management = E[Y | proposed] − E[Y | retrieval_only]
    """
    if not outcomes_proposed or not outcomes_retrieval:
        return {"estimand": "memory_management_effect", "value": None}

    mean_proposed = sum(o["success"] for o in outcomes_proposed) / len(outcomes_proposed)
    mean_retrieval = sum(o["success"] for o in outcomes_retrieval) / len(outcomes_retrieval)
    effect = mean_proposed - mean_retrieval

    return {
        "estimand": "memory_management_effect",
        "value": effect,
        "mean_proposed": mean_proposed,
        "mean_retrieval": mean_retrieval,
    }


def intervention_effect(
    outcomes_state_a: list[dict],
    outcomes_state_b: list[dict],
) -> dict:
    """E4: Intervention effect.

    τ_intervention = E[Y | memory_state_A] − E[Y | memory_state_B]
    """
    if not outcomes_state_a or not outcomes_state_b:
        return {"estimand": "intervention_effect", "value": None}

    mean_a = sum(o["success"] for o in outcomes_state_a) / len(outcomes_state_a)
    mean_b = sum(o["success"] for o in outcomes_state_b) / len(outcomes_state_b)
    effect = mean_a - mean_b

    return {
        "estimand": "intervention_effect",
        "value": effect,
        "mean_a": mean_a,
        "mean_b": mean_b,
    }


def category_specific_effect(
    outcomes_proposed: list[dict],
    outcomes_retrieval: list[dict],
    category: str,
) -> dict:
    """E5: Category-specific effect.

    τ_category = E[Y | proposed, category=c] − E[Y | retrieval_only, category=c]
    """
    prop_cat = [o for o in outcomes_proposed if o.get("category") == category]
    ret_cat = [o for o in outcomes_retrieval if o.get("category") == category]

    if not prop_cat or not ret_cat:
        return {"estimand": "category_specific_effect", "category": category, "value": None}

    mean_prop = sum(o["success"] for o in prop_cat) / len(prop_cat)
    mean_ret = sum(o["success"] for o in ret_cat) / len(ret_cat)
    effect = mean_prop - mean_ret

    return {
        "estimand": "category_specific_effect",
        "category": category,
        "value": effect,
        "mean_proposed": mean_prop,
        "mean_retrieval": mean_ret,
    }


def bootstrap_ci(
    values: list[float],
    n_bootstrap: int = 2000,
    seed: int = 12345,
) -> tuple[float, float]:
    """Compute bootstrap 95% confidence interval."""
    import random

    if not values:
        return (float("nan"), float("nan"))

    rng = random.Random(seed)
    means = []
    for _ in range(n_bootstrap):
        sample = [rng.choice(values) for _ in values]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int(0.025 * n_bootstrap)]
    hi = means[int(0.975 * n_bootstrap)]
    return (lo, hi)


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size for difference in proportions."""
    import math
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))
