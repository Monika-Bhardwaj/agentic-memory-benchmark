"""Counterfactual intervention.

The most important intervention: constructs paired conditions where everything
is identical except memory state. This establishes causal effects.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.interventions.base import Intervention, InterventionResult


@dataclass
class CounterfactualIntervention(Intervention):
    """Creates paired conditions with only memory state changed.

    Condition A: Memory says "Object = red" → Query → Expected: "red"
    Condition B: Memory says "Object = blue" → Query → Expected: "blue"

    What changes: Memory state (one item's content).
    What remains fixed: Task, query, model, observations, prompt, compute budget.

    Causal estimand: τ_counterfactual = E[Y | memory_A] − E[Y | memory_B]
    """

    entity: str = "Object"
    value_a: str = "red"
    value_b: str = "blue"
    query: str = "What color is the object?"

    def __init__(
        self,
        entity: str = "Object",
        value_a: str = "red",
        value_b: str = "blue",
        query: str = "What color is the object?",
        version: str = "v1",
    ):
        super().__init__(version)
        self.entity = entity
        self.value_a = value_a
        self.value_b = value_b
        self.query = query

    def apply(self, trajectory: dict, memory_state: dict) -> InterventionResult:
        """Apply counterfactual by changing one memory item's content."""
        # Determine which condition we're in based on memory_state
        condition = memory_state.get("condition", "A")

        if condition == "A":
            value = self.value_a
        else:
            value = self.value_b

        # Set the memory item
        memory_state["counterfactual_item"] = {
            "item_id": "m_cf",
            "content": f"{self.entity}: {value}.",
            "metadata": {
                "source": "counterfactual",
                "timestamp": 1,
                "confidence": 1.0,
                "adversarial": False,
                "authority": "system",
            },
        }

        # Update trajectory
        trajectory["counterfactual"] = {
            "entity": self.entity,
            "value_a": self.value_a,
            "value_b": self.value_b,
            "condition": condition,
            "expected_answer": value,
        }

        return InterventionResult(
            success=True,
            description=f"Counterfactual condition {condition}: {self.entity} = {value}",
            metadata={
                "entity": self.entity,
                "condition": condition,
                "value": value,
                "expected_answer": value,
            },
        )

    def apply_pair(self, trajectory: dict) -> tuple[dict, dict]:
        """Apply both conditions of the counterfactual pair.

        Returns:
            (trajectory_A, trajectory_B): Two trajectories identical except
            for the memory state.
        """
        import copy

        traj_a = copy.deepcopy(trajectory)
        traj_b = copy.deepcopy(trajectory)

        # Condition A
        mem_a = {"condition": "A"}
        self.apply(traj_a, mem_a)

        # Condition B
        mem_b = {"condition": "B"}
        self.apply(traj_b, mem_b)

        return traj_a, traj_b

    def describe(self) -> str:
        return f"Counterfactual: {self.entity} = {self.value_a} (A) vs {self.value_b} (B). Only memory state differs."

    def expected_effect(self) -> str:
        return "If memory has a causal effect, changing memory state from A to B should change the answer in the predicted direction. CCR ≥ 0.70 is consistent with a causal memory effect."

    def validate(self) -> list[str]:
        errors = []
        if not self.entity:
            errors.append("entity must be non-empty")
        if not self.value_a:
            errors.append("value_a must be non-empty")
        if not self.value_b:
            errors.append("value_b must be non-empty")
        if self.value_a == self.value_b:
            errors.append("value_a and value_b must differ")
        return errors
