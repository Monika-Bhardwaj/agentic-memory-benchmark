"""Baseline C — Structured memory.

Items are stored as typed records keyed by their ``LABEL`` (parsed deterministically
from the canonical ``LABEL: VALUE.`` content form). Minimal management by construction:

- update of an existing key replaces the single value for that key;
- an ``add`` whose label already exists is reconciled NEWEST-WINS (same key only);
- no provenance weighting, no consolidation, no history retention.

Note (documented prediction in milestone 1): the newest-wins rule means this baseline
systematically adopts the most recent claim, which is exactly wrong on adversarial
tasks where the injected claim is the newest. The benchmark is designed to expose this.
"""

from __future__ import annotations

from src.memory.base import Memory, MemoryItem, RetrievedItem, split_label_value
from src.utils.retrieval import TermIndex


class StructuredMemory(Memory):
    def __init__(self, seed: int, logger=None) -> None:
        super().__init__(seed, logger)
        # label -> item (single value per key)
        self._by_label: dict[str, MemoryItem] = {}
        # item_id -> label (index for update/forget by id)
        self._id_to_label: dict[str, str] = {}

    def _label_of(self, item: MemoryItem) -> str:
        label, _ = split_label_value(item.content)
        return label.lower()

    def add(self, item: MemoryItem) -> None:
        label = self._label_of(item)
        if label in self._by_label:
            old = self._by_label[label]
            self._log(
                op="add",
                item_id=item.item_id,
                label=label,
                reconciled=True,
                replaced=old.item_id,
                note="newest_wins_same_key",
            )
        else:
            self._log(op="add", item_id=item.item_id, label=label, reconciled=False)
        self._by_label[label] = item
        self._id_to_label[item.item_id] = label

    def update(self, item_id: str, item: MemoryItem) -> None:
        if item_id not in self._id_to_label:
            self._log(op="update", item_id=item_id, note="target_not_found_forced_add")
            self.add(item)
            return
        old_label = self._id_to_label[item_id]
        del self._id_to_label[item_id]
        del self._by_label[old_label]
        label = self._label_of(item)
        self._by_label[label] = item
        self._id_to_label[item.item_id] = label
        self._log(op="update", item_id=item_id, label=label)

    def forget(self, item_id: str) -> None:
        label = self._id_to_label.pop(item_id, None)
        existed = label is not None
        if existed:
            self._by_label.pop(label, None)
        self._log(op="forget", item_id=item_id, executed=existed)

    def retrieve(self, query: str, top_k: int) -> list[RetrievedItem]:
        if not self._by_label:
            self._log(op="retrieve", query=query, top_k=top_k, returned=[])
            return []
        labels = list(self._by_label.keys())
        docs = {label: f"{label} {it.content}" for label, it in self._by_label.items()}
        index = TermIndex(docs)
        ranked = index.rank(query, labels)
        picked = ranked[: max(top_k, 0)] if top_k >= 0 else ranked
        result = [
            RetrievedItem(
                item_id=self._by_label[label].item_id,
                content=self._by_label[label].content,
                metadata=self._by_label[label].metadata,
                score=score,
                rank=rank,
            )
            for rank, (label, score) in enumerate(picked)
        ]
        self._log(op="retrieve", query=query, top_k=top_k, returned=[r.item_id for r in result])
        return result

    def inspect(self) -> list[MemoryItem]:
        return list(self._by_label.values())