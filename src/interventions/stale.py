"""Stale/conflicting memory intervention.

Creates conditions where memory contains information that was once correct
but has become outdated.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.interventions.base import Intervention, InterventionResult


@dataclass
class StaleConflictIntervention(Intervention):
    """Creates conflicting memory entries with no authoritative directive.

    Event sequence:
        t=1: "Object A is at location X" → memory write (m1)
        t=2: "Object A is now at location Y" → memory write (m2)
        ...
        t=n: "Where is Object A?" → query

    The system must resolve by recency/authority.
    """

    entity: str = "Object A"
    old_value: str = "location X"
    new_value: str = "location Y"
    resolution: str = "recency"  # "recency", "authority"

    def __init__(
        self,
        entity: str = "Object A",
        old_value: str = "location X",
        new_value: str = "location Y",
        resolution: str = "recency",
        version: str = "v1",
    ):
        super().__init__(version)
        self.entity = entity
        self.old_value = old_value
        self.new_value = new_value
        self.resolution = resolution

    def apply(self, trajectory: dict, memory_state: dict) -> InterventionResult:
        """Add conflicting memory entries to the trajectory."""
        events = trajectory.get("events", [])

        # Add initial observation
        events.insert(0, {
            "event_id": "e_stale_1",
            "kind": "user_message",
            "text": f"{self.entity} is at {self.old_value}.",
            "item": {
                "item_id": "m_stale_1",
                "content": f"{self.entity}: {self.old_value}.",
                "metadata": {
                    "source": "user",
                    "timestamp": 1,
                    "confidence": 0.9,
                    "adversarial": False,
                    "authority": "user",
                },
            },
        })

        # Add conflicting observation
        events.insert(1, {
            "event_id": "e_stale_2",
            "kind": "user_message",
            "text": f"{self.entity} is now at {self.new_value}.",
            "item": {
                "item_id": "m_stale_2",
                "content": f"{self.entity}: {self.new_value}.",
                "metadata": {
                    "source": "user",
                    "timestamp": 2,
                    "confidence": 0.9,
                    "adversarial": False,
                    "authority": "user",
                },
            },
        })

        trajectory["events"] = events
        trajectory["conflict"] = {
            "entity": self.entity,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "resolution": self.resolution,
        }

        return InterventionResult(
            success=True,
            description=f"Created stale conflict: {self.entity} = {self.old_value} vs {self.new_value}",
            metadata={
                "entity": self.entity,
                "old_value": self.old_value,
                "new_value": self.new_value,
                "resolution": self.resolution,
            },
        )

    def describe(self) -> str:
        return f"Stale conflict: {self.entity} was {self.old_value}, now {self.new_value}. Resolve by {self.resolution}."

    def expected_effect(self) -> str:
        return "The system should resolve toward the more recent/authoritative value. Failure = STALE_MEMORY_FAILURE."

    def validate(self) -> list[str]:
        errors = []
        if not self.entity:
            errors.append("entity must be non-empty")
        if not self.old_value:
            errors.append("old_value must be non-empty")
        if not self.new_value:
            errors.append("new_value must be non-empty")
        if self.old_value == self.new_value:
            errors.append("old_value and new_value must differ")
        if self.resolution not in ("recency", "authority"):
            errors.append("resolution must be 'recency' or 'authority'")
        return errors
