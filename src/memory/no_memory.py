"""Baseline A — No persistent memory.

Implements the interface for harness uniformity; every operation is a no-op and
retrieval always returns nothing. The agent therefore sees only the current
single-turn context (posts to the model are never accumulated).
"""

from __future__ import annotations

from src.memory.base import Memory, MemoryItem, RetrievedItem


class NoMemory(Memory):
    def add(self, item: MemoryItem) -> None:
        self._log(op="add", item_id=item.item_id, executed=False)

    def update(self, item_id: str, item: MemoryItem) -> None:
        self._log(op="update", item_id=item_id, executed=False, content=item.content)

    def forget(self, item_id: str) -> None:
        self._log(op="forget", item_id=item_id, executed=False)

    def retrieve(self, query: str, top_k: int) -> list[RetrievedItem]:
        self._log(op="retrieve", query=query, top_k=top_k, returned=[])
        return []

    def inspect(self) -> list[MemoryItem]:
        return []