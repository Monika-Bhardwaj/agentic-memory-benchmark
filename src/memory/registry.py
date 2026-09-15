"""System registry — the single place mapping experiment system ids to factories.

The ``full_context`` row is not a different implementation: it is naive retrieval with
``retrieval_top_k = all`` (the harness passes the store size). This keeps the
comparison clean and makes the context-confound control one config knob.
"""

from __future__ import annotations

from src.memory.base import MemoryLogger
from src.memory.naive_retrieval import NaiveRetrieval
from src.memory.no_memory import NoMemory
from src.memory.sacam_v0 import SACAMv0
from src.memory.sacam_v1 import SACAMv1
from src.memory.structured_memory import StructuredMemory

SYSTEM_DESCRIPTIONS = {
    "no_memory": "A - No persistent memory",
    "naive_retrieval": "B - Naive retrieval memory",
    "structured_memory": "C - Structured memory",
    "sacam_v0": "D - SACAM v0 (placeholder, read-time management)",
    "sacam_v1": "D2 - SACAM v1 (v0.2 provenance-aware supersession fix)",
    "full_context": "Control - naive retrieval with top_k = all",
}


def build_system(system_id: str, seed: int, logger: MemoryLogger, weights: dict | None = None) -> object:
    if system_id == "no_memory":
        return NoMemory(seed, logger)
    if system_id == "naive_retrieval":
        return NaiveRetrieval(seed, logger)
    if system_id == "structured_memory":
        return StructuredMemory(seed, logger)
    if system_id == "sacam_v0":
        return SACAMv0(seed, logger, weights=weights)
    if system_id == "sacam_v1":
        return SACAMv1(seed, logger, weights=weights)
    if system_id == "full_context":
        return NaiveRetrieval(seed, logger)
    raise KeyError(f"unknown system: {system_id!r}")


def system_available(system_id: str) -> bool:
    return system_id in SYSTEM_DESCRIPTIONS