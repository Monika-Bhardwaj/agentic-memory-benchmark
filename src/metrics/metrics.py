"""Primary and secondary metrics (frozen definitions in docs/metrics.md).

All metrics are pure functions over per-cell ``TaskOutcome`` records.
"""

from __future__ import annotations

import statistics
from collections import Counter, defaultdict

from src.evaluation.outcome import TaskOutcome

MANAGEMENT_CRITICAL_CATEGORIES = {"updating", "stale_conflict", "forgetting", "adversarial"}


def tsr_for_run(outcomes: list[TaskOutcome]) -> float:
    """Task Success Rate for one (system x seed) run over its task cells."""
    if not outcomes:
        return 0.0
    return sum(1 for o in outcomes if o.success) / len(outcomes)


def aggregate_tsr(all_outcomes: list[TaskOutcome]) -> dict:
    """Aggregate across seeds for a system: per-run rates + mean + spread."""
    runs: dict[tuple[str, int], list[TaskOutcome]] = {}
    for o in all_outcomes:
        runs.setdefault((o.system, o.seed), []).append(o)
    per_seed = {k: tsr_for_run(v) for k, v in sorted(runs.items())}
    rates = list(per_seed.values())
    return {
        "n_seeds": len(rates),
        "per_seed": {f"{s}/{sd}": r for (s, sd), r in per_seed.items()},
        "mean": statistics.mean(rates) if rates else 0.0,
        "stdev": statistics.stdev(rates) if len(rates) > 1 else 0.0,
        "min": min(rates) if rates else 0.0,
        "max": max(rates) if rates else 0.0,
    }


def category_success_rates(outcomes: list[TaskOutcome]) -> dict[str, dict]:
    per_cat: dict[str, list[TaskOutcome]] = defaultdict(list)
    for o in outcomes:
        per_cat[o.category].append(o)
    result = {}
    for cat, cells in sorted(per_cat.items()):
        result[cat] = {
            "n": len(cells),
            "success_rate": sum(1 for o in cells if o.success) / len(cells),
        }
    return result


def management_critical_score(outcomes: list[TaskOutcome]) -> float:
    cells = [o for o in outcomes if o.category in MANAGEMENT_CRITICAL_CATEGORIES]
    if not cells:
        return 0.0
    return sum(1 for o in cells if o.success) / len(cells)


def failure_category_counts(outcomes: list[TaskOutcome]) -> dict:
    counts: Counter = Counter()
    for o in outcomes:
        if not o.success:
            counts[o.primary_failure_label or "UNLABELED"] += 1
            counts["ALL_FAILURES"] += 1
    counts["ALL_TASKS"] = len(outcomes)
    return dict(counts)


def retrieval_inclusion_rate(outcomes: list[TaskOutcome]) -> dict:
    """Fraction of cells where all required item ids appear in the retrieved set."""
    eligible = [o for o in outcomes if o.required_ids]
    if not eligible:
        return {"n": 0, "rate": None}
    ok = sum(1 for o in eligible if all(rid in o.retrieved_ids for rid in o.required_ids))
    return {"n": len(eligible), "rate": ok / len(eligible)}


def poison_acceptance_rate(outcomes: list[TaskOutcome]) -> dict:
    """Adversarial cells whose answer contains a poisoned (forbidden) value, and
    adversarial cells success among those where the trusted item was retrieved."""
    ads = [o for o in outcomes if o.category == "adversarial"]
    if not ads:
        return {"n": 0}
    accepted = 0
    for o in ads:
        if o.primary_failure_label == "ADVERSARIAL_MEMORY_FAILURE":
            accepted += 1
        elif o.primary_failure_label in ("RETRIEVAL_FAILURE", "IRRELEVANT_MEMORY_INTERFERENCE"):
            # not an agent-side acceptance; skip counting
            pass
    trustable = [o for o in ads if all(rid in o.retrieved_ids for rid in o.required_ids)]
    return {
        "n": len(ads),
        "acceptance_count": accepted,
        "acceptance_rate": accepted / len(ads),
        "n_trustable": len(trustable),
        "success_rate_when_trusted_retrieved": (
            sum(1 for o in trustable if o.success) / len(trustable) if trustable else None
        ),
    }


def token_overhead_summary(outcomes: list[TaskOutcome]) -> dict:
    vals = [o.memory_section_tokens_est for o in outcomes]
    return {
        "n": len(vals),
        "mean_tokens_est": statistics.mean(vals) if vals else 0.0,
        "max_tokens_est": max(vals) if vals else 0,
    }


def store_growth_summary(outcomes: list[TaskOutcome]) -> dict:
    vals = [o.store_size_at_query for o in outcomes]
    return {
        "n": len(vals),
        "mean": statistics.mean(vals) if vals else 0.0,
        "max": max(vals) if vals else 0,
    }