"""Causal memory evaluation experiment runner.

Supports v1 tasks with multimodal observations and causal interventions.
Usage::

    python experiments/run_causal.py --config configs/causal_dev.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.agents.harness import AgentHarness
from src.agents.models import build_model
from src.config import load_config
from src.evaluation.outcome import TaskOutcome
from src.memory.registry import build_system, system_available
from src.metrics.metrics import (
    aggregate_tsr,
    category_success_rates,
    management_critical_score,
)
from src.tasks.v1_loader import load_v1_tasks
from src.utils.hashing import file_sha256


def _ts() -> str:
    return datetime.now(timezone.utc).isoformat()


def _git_commit() -> str:
    try:
        import subprocess
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                             capture_output=True, text=True, timeout=5)
        return (out.stdout.strip() if out.returncode == 0 else "unknown")
    except Exception:
        return "unknown"


def run_causal(config_path: Path, seed_override: int | None = None, system_override: str | None = None) -> None:
    """Run causal memory evaluation experiment."""
    cfg = load_config(config_path)

    # Fail-closed: reject unknown phases
    if cfg.phase not in ("dev", "protected"):
        raise RuntimeError(
            f"UNKNOWN PHASE: {cfg.phase!r}. Only 'dev' or 'protected' are allowed."
        )

    # Fail-closed: reject protected runs without explicit authorization
    if cfg.phase == "protected":
        if cfg.authorization_approved is not True:
            raise RuntimeError(
                "PROTECTED RUN BLOCKED: authorization_approved is not True. "
                "Set authorization_approved: true in config with explicit approval."
            )
        # Reject unauthorized protected overrides
        if seed_override is not None or system_override is not None:
            raise RuntimeError(
                "PROTECTED RUN BLOCKED: seed/system overrides are not allowed "
                "for protected execution. Use the frozen configuration as-is."
            )
        # Require explicit protocol_version for protected configs
        # (not inherited from default)
        import yaml as _yaml
        with open(config_path, "r", encoding="utf-8") as fh:
            raw = _yaml.safe_load(fh) or {}
        exp_block = raw.get("experiment", {})
        if "protocol_version" not in exp_block:
            raise RuntimeError(
                "PROTECTED RUN BLOCKED: protocol_version must be explicitly set "
                "in the protected config, not inherited from default."
            )
        if cfg.protocol_version != "v0.2":
            raise RuntimeError(
                f"PROTECTED RUN BLOCKED: protocol_version must be v0.2, got {cfg.protocol_version}"
            )

    tasks, benchmark_hash = load_v1_tasks()
    exp_hash = cfg.hash()
    exp_id = f"{cfg.name}_{exp_hash[:8]}"
    base_dir = ROOT / cfg.results_dir / "raw" / exp_id

    if cfg.tasks_subset:
        tasks = [t for t in tasks if t["task_id"] in cfg.tasks_subset]

    # Filter by split
    if cfg.phase == "dev":
        tasks = [t for t in tasks if t["seed"] < 5000]
    elif cfg.phase == "protected":
        tasks = [t for t in tasks if t["seed"] >= 5000]

    seeds = [seed_override] if seed_override is not None else cfg.seeds
    systems = [system_override] if system_override else cfg.systems

    for sys_id in systems:
        if not system_available(sys_id):
            raise KeyError(f"unknown system: {sys_id}")

    all_outcomes: list[dict] = []
    summary: dict[tuple[str, int], list[TaskOutcome]] = {}

    pre_reg = {
        "experiment_id": exp_id,
        "protocol_version": cfg.protocol_version,
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
        "phase": cfg.phase,
    }

    # Write pre-registration if not exists
    pre_reg_path = base_dir / "pre_registration.json"
    if not pre_reg_path.exists():
        base_dir.mkdir(parents=True, exist_ok=True)
        with open(pre_reg_path, "w", encoding="utf-8") as fh:
            json.dump(pre_reg, fh, indent=2, ensure_ascii=False)

    for seed in seeds:
        for sys_id in systems:
            print(f"[{sys_id} seed={seed}] running {len(tasks)} tasks...", flush=True)
            run_id = f"{sys_id}_{seed}"
            run_dir = base_dir / run_id

            # Write config and metadata
            config_path = run_dir / "config.yaml"
            if not config_path.exists():
                run_dir.mkdir(parents=True, exist_ok=True)
                import yaml
                with open(config_path, "w", encoding="utf-8") as fh:
                    yaml.dump({"config": cfg.frozen_dict()}, fh, default_flow_style=False)

            meta_path = run_dir / "metadata.json"
            if not meta_path.exists():
                with open(meta_path, "w", encoding="utf-8") as fh:
                    json.dump({
                        "run_id": run_id,
                        "experiment_id": exp_id,
                        "system": sys_id,
                        "seed": seed,
                        "git_commit": _git_commit(),
                        "timestamp_start": _ts(),
                    }, fh, indent=2, ensure_ascii=False)

            run_outcomes: list[TaskOutcome] = []
            harness = AgentHarness(build_model(cfg.model, cfg.harness), prompt_version=cfg.prompt_version)

            for task in tasks:
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

            # Append outcomes
            outcomes_path = run_dir / "outcomes.jsonl"
            with open(outcomes_path, "a", encoding="utf-8") as fh:
                for o in run_outcomes:
                    fh.write(json.dumps(o.to_dict(), ensure_ascii=False) + "\n")

            sr = aggregate_tsr(run_outcomes)
            print(f"  TSR = {sr['mean']:.3f}", flush=True)

    # Write all outcomes
    all_outcomes_path = base_dir / "all_outcomes.jsonl"
    if not all_outcomes_path.exists():
        with open(all_outcomes_path, "w", encoding="utf-8") as fh:
            for o in all_outcomes:
                fh.write(json.dumps(o, ensure_ascii=False) + "\n")

    _print_table(summary, cfg.systems, seeds)
    print(f"\nRaw results: {base_dir}")


def _print_table(summary: dict, systems: list[str], seeds: list[int]) -> None:
    print("\n===== Summary (across seeds) =====")
    print(f"{'System':<25} {'TSR mean':>10} {'Std':>8} {'MCS':>8}")
    print("-" * 55)
    for sys_id in systems:
        run_cells = [(k, v) for k, v in summary.items() if k[0] == sys_id]
        outcomes = [o for _, cells in run_cells for o in cells]
        if not outcomes:
            continue
        sr = aggregate_tsr(outcomes)
        mcs = management_critical_score(outcomes)
        print(f"{sys_id:<25} {sr['mean']:10.3f} {sr['stdev']:8.3f} {mcs:8.3f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Causal memory evaluation runner")
    parser.add_argument("--config", required=True, help="path to YAML experiment config")
    parser.add_argument("--seed", type=int, default=None, help="override seed")
    parser.add_argument("--system", default=None, help="run a single system only")
    args = parser.parse_args()
    run_causal(Path(args.config), seed_override=args.seed, system_override=args.system)


if __name__ == "__main__":
    main()
