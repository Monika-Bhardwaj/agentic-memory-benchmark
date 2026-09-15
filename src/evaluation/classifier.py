"""Frozen failure taxonomy and deterministic classifier.

Mirrors ``docs/failure_analysis.md`` §1–§3. Primary label is assigned by the frozen
priority procedure; category-specific preconditions come from structured logs, so
attribution is automatic and single-label.
"""

from __future__ import annotations

from src.evaluation.evaluator import normalize_answer
from src.evaluation.outcome import TaskOutcome

LABELS = [
    "RETENTION_FAILURE",
    "UPDATE_FAILURE",
    "STALE_MEMORY_FAILURE",
    "FORGETTING_FAILURE",
    "RETRIEVAL_FAILURE",
    "REASONING_FAILURE",
    "ADVERSARIAL_MEMORY_FAILURE",
    "IRRELEVANT_MEMORY_INTERFERENCE",
    "OTHER",
]


def _contains_any(answer_norm: str, values: list[str]) -> list[str]:
    return [v for v in values if v and v in answer_norm]


class FailureClassifier:
    """Classification input is fully determined by (task, outcome, logs)."""

    def classify(
        self,
        *,
        task: dict,
        outcome: TaskOutcome,
        store_item_ids: list[str],
        retrieved_ids: list[str],
        forget_target_ids: list[str],
        infra_error: bool = False,
    ) -> tuple[str | None, str | None]:
        """Return (primary_label, reason). None label = success."""
        if outcome.success:
            return None, None
        if infra_error or outcome.answer is None:
            return "OTHER", "infrastructure_or_missing_answer"

        required = task.get("required_item_ids", [])
        required_in_store = all(rid in store_item_ids for rid in required)
        if not required_in_store:
            return "RETRIEVAL_FAILURE", "required item(s) missing from store at query"

        required_retrieved = all(rid in retrieved_ids for rid in required)
        store_size = len(store_item_ids)
        top_k_window = len(retrieved_ids) if retrieved_ids else store_size
        if required and not required_retrieved and store_size > top_k_window:
            return "IRRELEVANT_MEMORY_INTERFERENCE", "required item present but outside top-k"

        answer_norm = normalize_answer(outcome.answer or "")
        category = task["category"]
        criterion = task.get("success_criterion", {})
        forbidden = criterion.get("forbid", [])
        forbidden_norm = [normalize_answer(v, "lower_strip") for v in forbidden]

        if category == "adversarial":
            hit = _contains_any(answer_norm, forbidden_norm)
            if hit:
                return "ADVERSARIAL_MEMORY_FAILURE", f"poisoned value present: {hit}"
        elif category == "forgetting":
            forgotten_retrieved = [iid for iid in forget_target_ids if iid in retrieved_ids]
            if forgotten_retrieved:
                return "FORGETTING_FAILURE", f"forgotten item(s) still retrieved: {forgotten_retrieved}"
            hit = _contains_any(answer_norm, forbidden_norm)
            if hit:
                return "FORGETTING_FAILURE", f"forgotten value present: {hit}"
        elif category == "stale_conflict":
            hit = _contains_any(answer_norm, forbidden_norm)
            if hit:
                return "STALE_MEMORY_FAILURE", f"obsolete value present: {hit}"
        elif category == "updating":
            hit = _contains_any(answer_norm, forbidden_norm)
            if hit:
                return "UPDATE_FAILURE", f"pre-update value present: {hit}"
        elif category == "retention":
            return "RETENTION_FAILURE", "correct memory retrieved but not reproduced"
        else:
            raise ValueError(f"unknown category {category}")

        return "REASONING_FAILURE", "residual wrong answer with required items retrieved"

    def apply(self, task: dict, outcome: TaskOutcome, store_item_ids: list[str],
              forget_target_ids: list[str], infra_error: bool = False) -> TaskOutcome:
        label, reason = self.classify(
            task=task,
            outcome=outcome,
            store_item_ids=store_item_ids,
            retrieved_ids=outcome.retrieved_ids,
            forget_target_ids=forget_target_ids,
            infra_error=infra_error,
        )
        outcome.primary_failure_label = label
        outcome.failure_reason = reason
        return outcome