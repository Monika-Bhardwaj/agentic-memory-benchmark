"""Outcome records produced per task cell, feeding metrics and repro artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class TaskOutcome:
    task_id: str
    category: str
    difficulty: int
    system: str
    seed: int
    query: str
    answer: str | None
    success: bool
    primary_failure_label: str | None
    failure_reason: str | None
    retrieved_ids: list[str] = field(default_factory=list)
    required_ids: list[str] = field(default_factory=list)
    required_in_store: bool = True
    required_relevant_retrieved: bool = True
    store_size_at_query: int = 0
    memory_section_tokens_est: int = 0
    memory_section_chars: int = 0
    model_metadata: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)