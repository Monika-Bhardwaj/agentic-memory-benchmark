"""Formal intervention abstraction.

Interventions are deterministic and versioned. The intervention itself
must not inspect experimental outcomes.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class InterventionResult:
    """Result of applying an intervention."""
    success: bool
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Intervention(abc.ABC):
    """Base class for all interventions.

    An intervention manipulates memory state or task structure while
    holding other variables constant. Interventions are deterministic
    and versioned.
    """

    def __init__(self, version: str = "v1"):
        self._version = version

    @property
    def version(self) -> str:
        return self._version

    @abc.abstractmethod
    def apply(self, trajectory: dict, memory_state: dict) -> InterventionResult:
        """Apply the intervention to a trajectory and memory state.

        Args:
            trajectory: The task trajectory (events, observations, etc.)
            memory_state: The current memory state

        Returns:
            InterventionResult with success status and metadata
        """
        ...

    @abc.abstractmethod
    def describe(self) -> str:
        """Return a human-readable description of the intervention."""
        ...

    @abc.abstractmethod
    def expected_effect(self) -> str:
        """Return the expected effect of the intervention on behavior."""
        ...

    def validate(self) -> list[str]:
        """Validate that the intervention is correctly configured."""
        return []
