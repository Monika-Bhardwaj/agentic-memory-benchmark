"""Unified experiment runner.

Usage::

    python -m experiments.run --config configs/smoke.yaml [--seed 42] [--system sacam_v0]

Produces append-only raw results under ``results/raw/<experiment_id>/<run_id>/`` and
a compact summary table to stdout. Raw data is never overwritten.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.harness import AgentHarness
from src.agents.models import build_model
from src.config import ExperimentConfig, load_config, render_normalized_config
from src.evaluation.outcome import TaskOutcome
from src.memory.registry import build_system, system_available
from src.metrics.metrics import (
    aggregate_tsr,
    category_success_rates,
    failure_category_counts,
    management_critical_score,
    poison_acceptance_rate,
    retrieval_inclusion_rate,
    token_overhead_summary,
    store_growth_summary,
)
from src.tasks.loader import load_tasks


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")


def _write_once(path: Path, data: dict) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)


def run(config_path: Path, seed_override: int | None = None, system_override: str | None = None) -> None:
    cfg = load_config(config_path)
    benchmark, benchmark_hash = load_tasks()
    exp_hash = cfg.hash()
    exp_id = f"{cfg.name}_{exp_hash[:8]}"
    base_dir = ROOT / cfg.results_dir / "raw" / exp_id

    if cfg.tasks_subset:
        benchmark = [t for t in benchmark if t["task_id"] in cfg.tasks_subset]

    seeds = [seed_override] if seed_override is not None else cfg.seeds
    systems = [system_override] if system_override else cfg.systems
    for sys_id in systems:
        if not system_available(sys_id):
            raise KeyError(f"unknown system: {sys_id}")

    all_outcomes: list[dict] = []
    summary: dict[tuple[str, int], list[TaskOutcome]] = {}
    pre_reg = {
        "experiment_id": exp_id,
        "protocol_version": "v0.1",
        "benchmark_version": cfg.benchmark_version,
        "benchmark_hash": benchmark_hash,
        "config_hash": cfg.hash(),
        "seeds": seeds,
        "systems": systems,
        "model": cfg.model,
        "evaluation": cfg.evaluation,
        "prompt_version": cfg.prompt_version,
        "created_at": _ts(),
        "git_commit": _git_commit(),
    }
    _write_once(base_dir / "pre_registration.json", pre_reg)

    for seed in seeds:
        for sys_id in systems:
            print(f"[{sys_id} seed={seed}] running {len(benchmark)} tasks...", flush=True)
            run_id = f"{sys_id}_{seed}"
            run_dir = base_dir / run_id
            _write_once(run_dir / "config.yaml", {"config": cfg.frozen_dict()})
            _write_once(run_dir / "metadata.json", {
                "run_id": run_id, "experiment_id": exp_id, "system": sys_id, "seed": seed,
                "git_commit": _git_commit(), "timestamp_start": _ts(),
            })
            run_outcomes: list[TaskOutcome] = []
            harness = AgentHarness(build_model(cfg.model, cfg.harness), prompt_version=cfg.prompt_version)
            for task in benchmark:
                mem = build_system(sys_id, seed, None, weights=cfg.memory.get("sacam_weights", None))
                top_k_raw = cfg.memory.get("retrieval_top_k", 3)
                top_k = -1 if sys_id == "full_context" else int(top_k_raw)
                outcome = harness.run_task(
                    task, mem, seed=seed, system=sys_id,
                    retrieval_top_k=top_k,
                    respond_to_non_query_events=cfg.harness.get("respond_to_non_query_events", False),
                    model_temperature=float(cfg.model.get("temperature", 0)),
                    model_max_output_tokens=int(cfg.model.get("max_output_tokens", 512)),
                )
                run_outcomes.append(outcome)
                all_outcomes.append(outcome.to_dict())
            summary[(sys_id, seed)] = run_outcomes
            _append_jsonl(run_dir / "outcomes.jsonl", [o.to_dict() for o in run_outcomes])
            sr = aggregate_tsr(run_outcomes)
            print(f"  TSR = {sr['mean']:.3f}", flush=True)

    _write_once(base_dir / "all_outcomes.jsonl", all_outcomes)
    _print_table(summary, cfg.systems, seeds)
    print(f"\nRaw results: {base_dir}")


def _print_table(summary: dict, systems: list[str], seeds: list[int]) -> None:
    print("\n===== Summary (across seeds) =====")
    print(f"{'System':<25} {'TSR mean':>10} {'Std':>8} {'MCS':>8}")
    print("-" * 55)
    for sys_id in systems:
        run_cells = [(k, v) for k, v in summary.items() if k[0] == sys_id]
        outcomes = [o for _, cells in run_cells for o in cells]
        sr = aggregate_tsr(outcomes)
        mcs = management_critical_score(outcomes)
        print(f"{sys_id:<25} {sr['mean']:10.3f} {sr['stdev']:8.3f} {mcs:8.3f}")


def _git_commit() -> str:
    try:
        import subprocess
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5)
        return (out.stdout.strip() if out.returncode == 0 else "unknown")
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description="SACAM benchmark runner")
    parser.add_argument("--config", required=True, help="path to YAML experiment config")
    parser.add_argument("--seed", type=int, default=None, help="override seed")
    parser.add_argument("--system", default=None, help="run a single system only")
    args = parser.parse_args()
    run(Path(args.config), seed_override=args.seed, system_override=args.system)


if __name__ == "__main__":
    main()