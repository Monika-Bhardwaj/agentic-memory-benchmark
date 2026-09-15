"""SACAM v0 — minimal read-time management plugin.

This is the milestone-1 pre-registered placeholder only. It is NOT the full
sleep-consolidation architecture, which is explicitly out of scope for v0.1.
No v0 result can be read as evidence about the full SACAM architecture.

Frozen behaviour (all constants live in config ``sacam.weights``):
- add/update/forget compliance identical to every other system;
- canonical-consolidation: adding/updating a value marks earlier same-label items as
  ``superseded`` (kept for audit, strongly downranked at read time);
- provenance weighting: items with untrusted authority or confidence < 0.5 are
  strongly downranked at read time;
- recency weighting: mild boost for newer items.

The renderer is identical to all other systems: SACAM only changes *which* items are
retrieved and their order (rank), never the text shape injected into the prompt.
"""

from __future__ import annotations

from collections import OrderedDict

from src.memory.base import Memory, MemoryItem, RetrievedItem, split_label_value
from src.utils.retrieval import TermIndex


class SACAMv0(Memory):
    def __init__(self, seed: int, logger=None, weights: dict | None = None) -> None:
        super().__init__(seed, logger)
        weights = weights or {}
        self._w_superseded = float(weights.get("superseded", 0.1))
        self._w_untrusted = float(weights.get("untrusted", 0.1))
        self._w_recency = float(weights.get("recency", 0.2))
        self._items: "OrderedDict[str, MemoryItem]" = OrderedDict()
        self._superseded: set[str] = set()

    # -- management helpers ---------------------------------------------------
    def _label(self, item: MemoryItem) -> str:
        label, _ = split_label_value(item.content)
        return label.lower()

    def _consolidate(self, new_by_label: str, timestamp: int) -> None:
        """Mark older same-label items superseded (duplicate-key canonicalisation)."""
        for iid, item in self._items.items():
            if item.metadata.get("timestamp", 0) < timestamp and self._label(item) == new_by_label:
                self._superseded.add(iid)

    # -- store operations -----------------------------------------------------
    def add(self, item: MemoryItem) -> None:
        if item.item_id in self._items:
            self._log(op="add", item_id=item.item_id, note="overwrite_existing")
        self._items[item.item_id] = item
        self._superseded.discard(item.item_id)
        self._consolidate(self._label(item), int(item.metadata.get("timestamp", 0)))
        self._log(op="add", item_id=item.item_id, superseded_since=self._superseded.copy())

    def update(self, item_id: str, item: MemoryItem) -> None:
        if item_id in self._items:
            self._items[item_id] = item
            self._superseded.discard(item_id)
        else:
            self._items[item.item_id] = item
            self._log(op="update", item_id=item_id, note="target_not_found_forced_add")
        self._consolidate(self._label(item), int(item.metadata.get("timestamp", 0)))
        self._log(op="update", item_id=item.item_id, content=item.content)

    def forget(self, item_id: str) -> None:
        existed = self._items.pop(item_id, None) is not None
        self._superseded.discard(item_id)
        self._log(op="forget", item_id=item_id, executed=existed)

    # -- reading --------------------------------------------------------------
    def _multiplier(self, item: MemoryItem) -> float:
        mult = 1.0
        if item.item_id in self._superseded:
            mult *= self._w_superseded
        meta = item.metadata
        if meta.get("authority") == "untrusted" or float(meta.get("confidence", 1.0)) < 0.5:
            mult *= self._w_untrusted
        timestamps = [it.metadata.get("timestamp", 0) for it in self._items.values()]
        lo, hi = min(timestamps), max(timestamps)
        if hi > lo:
            age = (float(meta.get("timestamp", lo)) - lo) / (hi - lo)
            mult *= 1.0 + self._w_recency * age
        return mult

    def retrieve(self, query: str, top_k: int) -> list[RetrievedItem]:
        if not self._items:
            self._log(op="retrieve", query=query, top_k=top_k, returned=[])
            return []
        index = TermIndex({iid: it.content for iid, it in self._items.items()})
        decrease = {iid: self._multiplier(it) for iid, it in self._items.items()}
        ranked = index.rank(query, list(self._items.keys()), decrease=decrease)
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
        self._log(
            op="retrieve",
            query=query,
            top_k=top_k,
            returned=[r.item_id for r in result],
            multipliers={iid: self._multiplier(self._items[iid]) for iid in self._items},
        )
        return result

    def inspect(self) -> list[MemoryItem]:
        return list(self._items.values())