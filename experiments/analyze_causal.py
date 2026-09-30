"""Causal analysis for memory evaluation.

Computes causal estimands, counterfactual consistency, and generates
the causal results table.

Usage::

    python experiments/analyze_causal.py --config configs/causal_dev.yaml
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.causal.estimands import (
    average_memory_effect,
    bootstrap_ci,
    category_specific_effect,
    cohens_h,
    intervention_effect,
    memory_management_effect,
    retrieval_effect,
)
from src.causal.consistency import counterfactual_consistency_rate
from src.config import load_config
from src.metrics.metrics import MANAGEMENT_CRITICAL_CATEGORIES, aggregate_tsr, category_success_rates
from src.utils.hashing import file_sha256


def _load_cells(exp_dir: Path) -> list[dict]:
    cells: list[dict] = []
    for run_dir in sorted(exp_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        fp = run_dir / "outcomes.jsonl"
        if not fp.exists():
            continue
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                cells.append(json.loads(line))
    return cells


def _by(cells, key):
    d: dict = defaultdict(list)
    for c in cells:
        d[c[key]].append(c)
    return d


def _mean_tsr(cells_for_system: list[dict]) -> dict:
    from src.evaluation.outcome import TaskOutcome
    outcomes = [TaskOutcome(**c) for c in cells_for_system]
    return aggregate_tsr(outcomes)


def _mcs(cells_for_system: list[dict]) -> float:
    crit = [c for c in cells_for_system if c["category"] in MANAGEMENT_CRITICAL_CATEGORIES]
    if not crit:
        return 0.0
    return sum(1 for c in crit if c["success"]) / len(crit)


def main() -> None:
    parser = argparse.ArgumentParser(description="Causal memory evaluation analysis")
    parser.add_argument("--config", required=True)
    parser.add_argument("--experiment-id", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    exp_id = args.experiment_id or f"{cfg.name}_{cfg.hash()[:8]}"
    raw_dir = ROOT / cfg.results_dir / "raw" / exp_id

    if not raw_dir.exists():
        print(f"No raw results at {raw_dir}. Run experiments/run_causal.py first.", file=sys.stderr)
        sys.exit(1)

    cells = _load_cells(raw_dir)
    by_sys = _by(cells, "system")
    systems = [s for s in cfg.systems if s in by_sys]

    # Compute basic metrics
    tables: dict = {}
    for s in systems:
        sc = by_sys[s]
        tables[s] = {
            "n_cells": len(sc),
            "tsr": _mean_tsr(sc),
            "mcs": _mcs(sc),
            "by_category": category_success_rates([_as_outcome(c) for c in sc]),
        }

    # Compute causal estimands
    causal_effects = {}
    if "no_memory" in by_sys and "naive_retrieval" in by_sys:
        causal_effects["memory_vs_no_memory"] = average_memory_effect(
            by_sys["naive_retrieval"], by_sys["no_memory"]
        )
    if "naive_retrieval" in by_sys and "sacam_v1" in by_sys:
        causal_effects["management_vs_retrieval"] = memory_management_effect(
            by_sys["sacam_v1"], by_sys["naive_retrieval"]
        )
    if "no_memory" in by_sys and "sacam_v1" in by_sys:
        causal_effects["proposed_vs_no_memory"] = average_memory_effect(
            by_sys["sacam_v1"], by_sys["no_memory"]
        )

    # Category-specific effects
    category_effects = {}
    if "naive_retrieval" in by_sys and "sacam_v1" in by_sys:
        for cat in MANAGEMENT_CRITICAL_CATEGORIES:
            category_effects[cat] = category_specific_effect(
                by_sys["sacam_v1"], by_sys["naive_retrieval"], cat
            )

    # Counterfactual consistency
    ccr_result = None
    cf_cells = [c for c in cells if c.get("category") == "counterfactual"]
    if cf_cells:
        # Group by task_id and system
        cf_by_task = defaultdict(list)
        for c in cf_cells:
            cf_by_task[(c["task_id"], c["system"])].append(c)

        paired_outcomes = []
        for (task_id, system), task_cells in cf_by_task.items():
            if len(task_cells) >= 2:
                # Sort by seed to get pairs
                task_cells.sort(key=lambda c: c["seed"])
                for i in range(0, len(task_cells) - 1, 2):
                    paired_outcomes.append({
                        "condition_a": task_cells[i],
                        "condition_b": task_cells[i + 1],
                        "expected_direction": "A",
                    })

        if paired_outcomes:
            ccr_result = counterfactual_consistency_rate(paired_outcomes)

    # Build output
    out = {
        "experiment_id": exp_id,
        "config_hash": cfg.hash(),
        "benchmark_hash": file_sha256(ROOT / "benchmark" / "v1" / "tasks.jsonl"),
        "phase": cfg.phase,
        "metrics": tables,
        "causal_effects": causal_effects,
        "category_effects": category_effects,
        "counterfactual_consistency": ccr_result,
    }

    # Write output
    out_dir = ROOT / cfg.results_dir / "processed" / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "causal_tables.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)

    _write_causal_report(out_dir / "causal_report.md", out)
    print(f"Causal analysis written to {out_dir}")


def _as_outcome(c: dict):
    from src.evaluation.outcome import TaskOutcome
    return TaskOutcome(**c)


def _write_causal_report(path: Path, out: dict) -> None:
    lines = [
        f"# Causal Analysis — {out['experiment_id']}",
        "",
        f"- phase: `{out['phase']}`",
        f"- config hash: `{out['config_hash']}`",
        f"- benchmark hash: `{out['benchmark_hash']}`",
        "",
        "## Primary Metric (TSR)",
        "",
        "| System | n | Mean | Std | MCS |",
        "|---|---|---|---|---|",
    ]
    for s, m in out["metrics"].items():
        t = m["tsr"]
        lines.append(f"| {s} | {m['n_cells']} | {t['mean']:.3f} | {t['stdev']:.3f} | {m['mcs']:.3f} |")

    lines += ["", "## Causal Effects", ""]
    for name, effect in out.get("causal_effects", {}).items():
        if effect.get("value") is not None:
            lines.append(f"- **{name}**: {effect['value']:.4f}")
        else:
            lines.append(f"- **{name}**: N/A")

    lines += ["", "## Category-Specific Effects", ""]
    for cat, effect in out.get("category_effects", {}).items():
        if effect.get("value") is not None:
            lines.append(f"- **{cat}**: {effect['value']:.4f}")

    if out.get("counterfactual_consistency"):
        ccr = out["counterfactual_consistency"]
        lines += [
            "",
            "## Counterfactual Consistency",
            "",
            f"- CCR: {ccr.get('ccr', 'N/A')}",
            f"- N pairs: {ccr.get('n_pairs', 0)}",
            f"- N consistent: {ccr.get('n_consistent', 0)}",
            f"- Interpretation: {ccr.get('interpretation', 'N/A')}",
        ]

    lines += [
        "",
        "> This analysis is generated automatically from raw results.",
        "> No manual edits.",
    ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
