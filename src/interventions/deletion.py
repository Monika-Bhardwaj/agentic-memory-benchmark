"""Deletion intervention.

Defines tasks where information should be removed from persistent memory.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.interventions.base import Intervention, InterventionResult


@dataclass
class DeletionIntervention(Intervention):
    """Removes a specified item from memory.

    Event sequence:
        t=1: "The meeting is at 3pm" → memory write (m1)
        t=2: "Forget the meeting time" → memory_forget (m1)
        ...
        t=n: "When is the meeting?" → query

    Operational definition: Deletion means the specified information is removed
    or rendered unavailable through the persistent-memory interface.

    Important: We do NOT claim the model has "forgotten" — only the external
    memory store is modified.
    """

    item_id: str = "m1"
    item_content: str = "Meeting time: 3pm."
    forget_text: str = "Please forget the meeting time."

    def __init__(
        self,
        item_id: str = "m1",
        item_content: str = "Meeting time: 3pm.",
        forget_text: str = "Please forget the meeting time.",
        version: str = "v1",
    ):
        super().__init__(version)
        self.item_id = item_id
        self.item_content = item_content
        self.forget_text = forget_text

    def apply(self, trajectory: dict, memory_state: dict) -> InterventionResult:
        """Add a forget directive to the trajectory."""
        events = trajectory.get("events", [])

        # Add the item to be forgotten
        events.insert(0, {
            "event_id": "e_del_1",
            "kind": "user_message",
            "text": self.item_content,
            "item": {
                "item_id": self.item_id,
                "content": self.item_content,
                "metadata": {
                    "source": "user",
                    "timestamp": 1,
                    "confidence": 1.0,
                    "adversarial": False,
                    "authority": "user",
                },
            },
        })

        # Add the forget directive
        events.insert(1, {
            "event_id": "e_del_2",
            "kind": "memory_forget",
            "text": self.forget_text,
            "item_id": self.item_id,
        })

        trajectory["events"] = events
        trajectory["deletion"] = {
            "item_id": self.item_id,
            "item_content": self.item_content,
        }

        return InterventionResult(
            success=True,
            description=f"Added deletion directive for {self.item_id}",
            metadata={"item_id": self.item_id, "item_content": self.item_content},
        )

    def describe(self) -> str:
        return f"Deletion: {self.item_id} = '{self.item_content}' should be forgotten"

    def expected_effect(self) -> str:
        return "The forgotten item should not appear in retrieval results. The final answer should not contain the forgotten value. Failure = FORGETTING_FAILURE."

    def validate(self) -> list[str]:
        errors = []
        if not self.item_id:
            errors.append("item_id must be non-empty")
        if not self.item_content:
            errors.append("item_content must be non-empty")
        return errors
