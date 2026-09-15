"""Common memory interface and data structures.

All memory systems must implement ``Memory`` and be interchangeable drop-in for the
harness. The harness emits the frozen directive stream (identical for every system);
systems differ only in *representation, storage, retrieval and management*.

This mirrors the frozen contract in ``docs/architecture.md`` §2.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class MemoryItem:
    item_id: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_metadata(self, **overrides: Any) -> "MemoryItem":
        meta = dict(self.metadata)
        meta.update(overrides)
        return replace(self, metadata=meta)


@dataclass(frozen=True)
class RetrievedItem:
    item_id: str
    content: str
    metadata: dict[str, Any]
    score: float
    rank: int


class Memory(abc.ABC):
    """Frozen contract. ``seed`` is accepted for interface uniformity; systems must
    be deterministic under a given seed."""

    def __init__(self, seed: int, logger: "MemoryLogger | None" = None) -> None:
        self.seed = seed
        self._logger = logger or MemoryLogger()

    @abc.abstractmethod
    def add(self, item: MemoryItem) -> None: ...

    @abc.abstractmethod
    def update(self, item_id: str, item: MemoryItem) -> None: ...

    @abc.abstractmethod
    def forget(self, item_id: str) -> None: ...

    @abc.abstractmethod
    def retrieve(self, query: str, top_k: int) -> list[RetrievedItem]: ...

    @abc.abstractmethod
    def inspect(self) -> list[MemoryItem]: ...

    def _log(self, op: str, **kwargs: Any) -> None:
        self._logger.record(op=op, **kwargs)


@dataclass
class MemoryLogger:
    """Audit trail of every memory operation, for raw-log preservation and opaque
    failure attribution. Append-only in practice (see runner)."""

    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, **kwargs: Any) -> None:
        self.events.append(dict(kwargs))

    def snapshot(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self.events]

    def forget_target_ids(self) -> list[str]:
        return [e["item_id"] for e in self.events if e["op"] == "forget"]


# --- label parsing convention -------------------------------------------------
# v0.1 memory content uses the canonical form  ``LABEL: VALUE.``  so that structured
# and SACAM representations can extract an entity/slot deterministically.
# See benchmark/v0/SPEC.md §4 for the frozen convention.


def split_label_value(content: str) -> tuple[str, str]:
    """Return (label, value) from ``LABEL: VALUE`` content. Never raises.

    If no ':' is present the whole content is label and value''.
    """
    if ":" in content:
        label, value = content.split(":", 1)
        return label.strip(), value.strip().rstrip(".")
    return content.strip(), ""