"""Configuration loading, validation, and hashing.

Configs are YAML files committed under ``configs/``. A normalized (sorted-key) hash of
the effective config is captured per run. Defaults below are the frozen v0.1 values.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from src.utils.hashing import canonical_json, sha256_of

DEFAULT_SEEDS_SMOKE = [42, 7, 2024]
DEFAULT_SEEDS_FULL = [42, 7, 2024, 1337, 2718]

DEFAULT_MME = 0.05
DEFAULT_RETENTION_TOLERANCE = -0.05
DEFAULT_SACAM_WEIGHTS = {"superseded": 0.1, "untrusted": 0.1, "recency": 0.2}


@dataclass
class ExperimentConfig:
    name: str
    benchmark_version: str = "v0.1"
    phase: str = "smoke"  # or "full"
    seeds: list[int] = field(default_factory=lambda: list(DEFAULT_SEEDS_SMOKE))
    tasks_subset: list[str] = field(default_factory=list)  # task_ids to run ([] = all)
    systems: list[str] = field(default_factory=lambda: ["no_memory", "naive_retrieval", "structured_memory", "sacam_v0"])

    model: dict = field(default_factory=lambda: {"name": "mock_pattern_reader", "temperature": 0, "max_output_tokens": 512})
    provider: dict = field(default_factory=dict)

    memory: dict = field(default_factory=lambda: {
        "retrieval_top_k": 3,
        "memory_budget_items": 512,
        "full_context_top_k": "all",
        "sacam_weights": dict(DEFAULT_SACAM_WEIGHTS),
    })

    evaluation: dict = field(default_factory=lambda: {
        "primary_metric": "tsr",
        "mme": DEFAULT_MME,
        "retention_tolerance": DEFAULT_RETENTION_TOLERANCE,
    })

    harness: dict = field(default_factory=lambda: {
        "respond_to_non_query_events": False,
        "timeout_seconds": 60,
        "max_retries": 1,
    })

    prompt_version: str = "v0.1-p1"
    results_dir: str = "results"

    def frozen_dict(self) -> dict:
        return copy.deepcopy(asdict(self))

    def hash(self) -> str:
        return sha256_of(self.frozen_dict())

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.frozen_dict(), sort_keys=False, default_flow_style=False)


REQUIRED_KEYS = {"experiment", "model", "memory", "evaluation"}


def load_config(path: Path | str) -> ExperimentConfig:
    path = Path(path)
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    if not isinstance(raw, dict):
        raise ValueError("config root must be a mapping")
    missing = REQUIRED_KEYS - set(raw)
    if missing:
        raise ValueError(f"config missing required blocks: {sorted(missing)}")

    exp = raw["experiment"]
    seeds = list(exp.get("seeds", DEFAULT_SEEDS_SMOKE))
    if not seeds:
        raise ValueError("experiment.seeds must be non-empty")
    subset = list(exp.get("tasks_subset", []))

    cfg = ExperimentConfig(
        name=str(exp.get("name", "unnamed")),
        benchmark_version=str(exp.get("benchmark_version", "v0.1")),
        phase=str(exp.get("phase", "smoke")),
        seeds=seeds,
        tasks_subset=subset,
        systems=[str(s) for s in exp.get("systems", ["no_memory", "naive_retrieval", "structured_memory", "sacam_v0"])],
        model={k: v for k, v in raw.get("model", {}).items()},
        provider={k: v for k, v in raw.get("provider", {}).items()},
        memory={k: v for k, v in raw.get("memory", {}).items()},
        evaluation={k: v for k, v in raw.get("evaluation", {}).items()},
        harness={k: v for k, v in raw.get("harness", {}).items()},
        prompt_version=str(raw.get("prompt_version", "v0.1-p1")),
        results_dir=str(exp.get("results_dir", "results")),
    )
    cfg.memory.setdefault("sacam_weights", dict(DEFAULT_SACAM_WEIGHTS))
    cfg.memory.setdefault("retrieval_top_k", 3)
    cfg.memory.setdefault("full_context_top_k", "all")
    cfg.evaluation.setdefault("mme", DEFAULT_MME)
    cfg.evaluation.setdefault("retention_tolerance", DEFAULT_RETENTION_TOLERANCE)
    for sys_id in cfg.systems:
        assert sys_id in ("no_memory", "naive_retrieval", "structured_memory", "sacam_v0", "sacam_v1", "full_context"), sys_id
    return cfg


def render_normalized_config(cfg: ExperimentConfig) -> str:
    """For hashing/metadata, independent of local YAML formatting."""
    return canonical_json(cfg.frozen_dict())