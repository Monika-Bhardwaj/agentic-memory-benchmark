"""Baseline B — Naive retrieval memory.

Append items as-is; deterministic term-overlap retrieval of the top-k most similar
items; literal compliance with update/forget directives. Explicitly has NO reading-time
management: no recency weighting, no conflict handling, no provenance handling, no
consolidation. An update replaces the target item's content in place (same id).
"""

from __future__ import annotations

from collections import OrderedDict

from src.memory.base import Memory, MemoryItem, RetrievedItem
from src.utils.retrieval import TermIndex


class NaiveRetrieval(Memory):
    def __init__(self, seed: int, logger=None) -> None:
        super().__init__(seed, logger)
        self._items: "OrderedDict[str, MemoryItem]" = OrderedDict()

    # -- store operations -----------------------------------------------------
    def add(self, item: MemoryItem) -> None:
        if item.item_id in self._items and self._items[item.item_id] != item:
            self._log(op="add", item_id=item.item_id, note="overwrite_existing")
        self._items[item.item_id] = item
        self._log(op="add", item_id=item.item_id, content=item.content)

    def update(self, item_id: str, item: MemoryItem) -> None:
        if item_id in self._items:
            self._items[item_id] = item
            self._log(op="update", item_id=item_id, content=item.content)
        else:
            self.add(item)
            self._log(op="update", item_id=item_id, note="target_not_found_forced_add")

    def forget(self, item_id: str) -> None:
        existed = self._items.pop(item_id, None) is not None
        self._log(op="forget", item_id=item_id, executed=existed)

    # -- read operations ------------------------------------------------------
    def retrieve(self, query: str, top_k: int) -> list[RetrievedItem]:
        if not self._items:
            self._log(op="retrieve", query=query, top_k=top_k, returned=[])
            return []
        index = TermIndex({iid: it.content for iid, it in self._items.items()})
        ranked = index.rank(query, list(self._items.keys()))
        picked = ranked[: max(top_k, 0)] if top_k >= 0 else ranked
        result = [
            RetrievedItem(
                item_id=iid,
                content=self._items[iid].content,
                metadata=self._items[iid].metadata,
                score=score,
                rank=rank,
            )
            for rank, (iid, score) in enumerate(picked)
        ]
        self._log(op="retrieve", query=query, top_k=top_k, returned=[r.item_id for r in result])
        return result

    def inspect(self) -> list[MemoryItem]:
        return list(self._items.values())