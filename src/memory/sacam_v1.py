"""SACAM v0.2 — provenance-aware supersession (fix to v0's canonical-consolidation bug).

v0.1 finding (see research_review.md): v0 marked a higher-confidence claim as
``superseded`` the moment an untrusted, same-label impostor arrived (confidence 1.0 ->
0.1 multiplier; impostor confidence 0.2 with recency boosted above it). Adversarial TSR
collapsed to 0.07.

v1 fix: an older same-label claim is superseded only when the *new* claim is not weaker
(not lower-confidence / not lower-authority) than the old one. This preserves the
high-confidence record while retaining v0's provenance downweighting and recency boost
for genuinely untrusted or superseded content.

Trade-off (expected from the benchmark's own structure): adversarial recovers toward
the naive/full_context level, but stale_conflict where the *correct* update is itself
low-confidence will no longer be auto-adopted (the model must adjudicate via metadata,
as in naive retrieval). No fixed read-time policy wins both; that is the point of the
frozen two-axes failure structure.
"""

from __future__ import annotations

from src.memory.base import MemoryItem
from src.memory.sacam_v0 import SACAMv0

# authority -> additive strength bonus (aligned with the benchmark's metadata scale)
_AUTHORITY_BONUS = {
    "untrusted": -0.5,
    "junior": -0.2,
    "team": 0.3,
    "admin": 0.3,
    "high": 0.3,
}


class SACAMv1(SACAMv0):
    """Provenance-aware canonical-consolidation: never supersede a stronger claim."""

    def _strength(self, item: MemoryItem) -> float:
        meta = item.metadata
        conf = float(meta.get("confidence", 1.0))
        auth = str(meta.get("authority", "")).lower()
        return conf + _AUTHORITY_BONUS.get(auth, 0.0)

    def _consolidate(self, new_by_label: str, timestamp: int, new_item: MemoryItem | None = None) -> None:
        """Mark older same-label items superseded only if the new claim is not weaker."""
        new_strength = self._strength(new_item) if new_item is not None else float("inf")
        for iid, item in list(self._items.items()):
            if iid in self._superseded:
                continue
            if item.metadata.get("timestamp", 0) >= timestamp or self._label(item) != new_by_label:
                continue
            if new_strength >= self._strength(item):
                self._superseded.add(iid)

    def add(self, item: MemoryItem) -> None:
        if item.item_id in self._items:
            self._log(op="add", item_id=item.item_id, note="overwrite_existing")
        self._items[item.item_id] = item
        self._superseded.discard(item.item_id)
        self._consolidate(self._label(item), int(item.metadata.get("timestamp", 0)), new_item=item)
        self._log(op="add", item_id=item.item_id, superseded_since=self._superseded.copy())

    def update(self, item_id: str, item: MemoryItem) -> None:
        if item_id in self._items:
            self._items[item_id] = item
            self._superseded.discard(item_id)
        else:
            self._items[item.item_id] = item
            self._log(op="update", item_id=item_id, note="target_not_found_forced_add")
        self._consolidate(self._label(item), int(item.metadata.get("timestamp", 0)), new_item=item)
        self._log(op="update", item_id=item.item_id, content=item.content)