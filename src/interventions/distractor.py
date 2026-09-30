"""Distractor intervention.

Introduces irrelevant multimodal information that should not affect the answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.interventions.base import Intervention, InterventionResult


@dataclass
class DistractorIntervention(Intervention):
    """Adds irrelevant visual and textual distractors to a task.

    Control condition: No distractor; relevant info only.
    Distractor condition: Relevant info + irrelevant visual/textual distractors.

    What changes: Presence of distractor objects/facts.
    What remains fixed: Relevant information, query, model, budgets.
    """

    n_distractors: int = 1
    distractor_type: str = "visual"  # "visual", "textual", "both"

    def __init__(self, n_distractors: int = 1, distractor_type: str = "visual", version: str = "v1"):
        super().__init__(version)
        self.n_distractors = n_distractors
        self.distractor_type = distractor_type

    def apply(self, trajectory: dict, memory_state: dict) -> InterventionResult:
        """Add distractor events to the trajectory."""
        events = trajectory.get("events", [])
        distractor_events = []

        for i in range(self.n_distractors):
            distractor_events.append({
                "event_id": f"dist_{i}",
                "kind": "user_message",
                "text": f"Distractor information {i}: irrelevant detail.",
                "is_distractor": True,
            })

        # Insert distractors before the query
        new_events = []
        for event in events:
            if event.get("kind") == "query":
                new_events.extend(distractor_events)
            new_events.append(event)

        trajectory["events"] = new_events
        trajectory["distractor_event_ids"] = [e["event_id"] for e in distractor_events]

        return InterventionResult(
            success=True,
            description=f"Added {self.n_distractors} distractor(s) of type '{self.distractor_type}'",
            metadata={"n_distractors": self.n_distractors, "type": self.distractor_type},
        )

    def describe(self) -> str:
        return f"Distractor intervention: {self.n_distractors} irrelevant {self.distractor_type} distractor(s)"

    def expected_effect(self) -> str:
        return "A robust memory system should NOT be affected by distractors. Performance drop indicates perception, retrieval, or reasoning failure."

    def validate(self) -> list[str]:
        errors = []
        if self.n_distractors < 0:
            errors.append("n_distractors must be non-negative")
        if self.distractor_type not in ("visual", "textual", "both"):
            errors.append("distractor_type must be 'visual', 'textual', or 'both'")
        return errors
