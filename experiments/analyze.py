"""Milestone-3 (and later full-run) analysis + report generator.

Usage::

    python experiments/analyze.py --config configs/smoke.yaml [--experiment-id <id>]

Loads the append-only raw outcome cells, computes the frozen metrics and the
pre-registered E-rule checks (E1–E5), and writes:

    results/processed/<experiment_id>/tables.json
    results/processed/<experiment_id>/report.md

For phase ``smoke`` the E-rule rows are labelled ILLUSTRATIVE ONLY (the frozen rule
explicitly applies to the full benchmark run, docs/research_question.md §6).
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

from src.config import load_config
from src.metrics.metrics import MANAGEMENT_CRITICAL_CATEGORIES, aggregate_tsr, category_success_rates
from src.utils.hashing import file_sha256

MME = 0.05
RETENTION_TOLERANCE = -0.05
N = 2000


def _load_cells(exp_dir: Path) -> list[dict]:
    cells: list[dict] = []
    for run_dir in sorted(exp_dir.iterdir()):
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
    return aggregate_tsr([_as_outcome(c) for c in cells_for_system])


def _mcs(cells_for_system: list[dict]) -> float:
    crit = [c for c in cells_for_system if c["category"] in MANAGEMENT_CRITICAL_CATEGORIES]
    if not crit:
        return 0.0
    return sum(1 for c in crit if c["success"]) / len(crit)


def _tsr_retention(cells_for_system: list[dict]) -> float:
    ret = [c for c in cells_for_system if c["category"] == "retention"]
    if not ret:
        return 0.0
    return sum(1 for c in ret if c["success"]) / len(ret)


def _per_seed_tsr_diff(cells_sacam: list[dict], cells_naive: list[dict]) -> list[float]:
    by_seed_s = _by(cells_sacam, "seed")
    by_seed_n = _by(cells_naive, "seed")
    diffs = []
    for seed, scells in by_seed_s.items():
        ncells = by_seed_n.get(seed)
        if ncells:
            diffs.append(_mean_tsr(scells)["mean"] - _mean_tsr(ncells)["mean"])
    return diffs


def _bootstrap_interval(diffs: list[float]) -> tuple[float, float]:
    if not diffs:
        return (float("nan"), float("nan"))
    import random
    rng = random.Random(12345)
    means = []
    for _ in range(N):
        sample = [rng.choice(diffs) for _ in range(len(diffs))]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo = means[int(0.025 * N)]
    hi = means[int(0.975 * N)]
    return (lo, hi)


def _failure_shift(cells_sacam: list[dict], cells_naive: list[dict]) -> str:
    """E5: does SACAM's gain come mostly from fewer REASONING_FAILURE labels?"""
    from collections import Counter
    def count_delta(cells):
        cnt = Counter()
        for c in cells:
            if not c["success"]:
                cnt[c["primary_failure_label"] or "UNLABELED"] += 1
        return cnt
    d_s = count_delta(cells_sacam)
    d_n = count_delta(cells_naive)
    shift = {k: d_n[k] - d_s.get(k, 0) for k in set(d_n) | set(d_s) if d_n[k] - d_s.get(k, 0)}
    reasoning_saved = shift.get("REASONING_FAILURE", 0)
    mgmt_saved = sum(shift.get(k, 0) for k in
                     ("STALE_MEMORY_FAILURE", "FORGETTING_FAILURE",
                      "ADVERSARIAL_MEMORY_FAILURE", "UPDATE_FAILURE"))
    total_saved = sum(shift.values())
    dominated_by_reasoning = total_saved > 0 and reasoning_saved >= mgmt_saved
    return {
        "label_counts_naive": dict(d_n),
        "label_counts_sacam": dict(d_s),
        "shift": shift,
        "reasoning_saved": reasoning_saved,
        "management_saved": mgmt_saved,
        "total_saved": total_saved,
        "dominated_by_reasoning": dominated_by_reasoning,
    }


def _as_outcome(c: dict):
    from src.evaluation.outcome import TaskOutcome
    return TaskOutcome(**c)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--experiment-id", default=None)
    args = parser.parse_args()

    cfg = load_config(args.config)
    exp_id = args.experiment_id or f"{cfg.name}_{cfg.hash()[:8]}"
    raw_dir = ROOT / cfg.results_dir / "raw" / exp_id
    if not raw_dir.exists():
        print(f"No raw results at {raw_dir}. Run experiments/run.py first.", file=sys.stderr)
        sys.exit(1)

    cells = _load_cells(raw_dir)
    by_sys = _by(cells, "system")
    systems = [s for s in cfg.systems if s in by_sys]

    tables: dict = {}
    for s in systems:
        sc = by_sys[s]
        tables[s] = {
            "n_cells": len(sc),
            "tsr": _mean_tsr(sc),
            "mcs": _mcs(sc),
            "tsr_retention": _tsr_retention(sc),
            "by_category": category_success_rates([_as_outcome(c) for c in sc]),
            "failure_labels": {
                k: sum(1 for c in sc if not c["success"] and c["primary_failure_label"] == k)
                for k in set(c["primary_failure_label"] for c in sc if not c["success"])
            },
            "store_growth_max": max((c["store_size_at_query"] for c in sc), default=0),
            "memory_section_tokens_avg": round(
                statistics.mean(c["memory_section_tokens_est"] for c in sc), 1) if sc else 0,
            "retrieval_calls": 1 if sc else 0,
        }

    s_sam = tables.get("sacam_v0")
    s_naive = tables.get("naive_retrieval")
    s_full = tables.get("full_context")
    e_rules = {}
    if s_sam and s_naive and s_full:
        diffs_e1 = _per_seed_tsr_diff(by_sys.get("sacam_v0", []), by_sys.get("naive_retrieval", []))
        lo, hi = _bootstrap_interval(diffs_e1)
        dMCS_n = s_sam["mcs"] - s_naive["mcs"]
        dTSR_ret = s_sam["tsr_retention"] - s_naive.get("tsr_retention", 0)
        dMCS_full = s_sam["mcs"] - s_full["mcs"]
        e_rules = {
            "E1_direction": {
                "median_delta_per_seed": statistics.median(diffs_e1) if diffs_e1 else None,
                "per_seed_deltas": diffs_e1,
                "bootstrap_ci_95": [round(lo, 4), round(hi, 4)],
                "rule_hit": (statistics.median(diffs_e1) if diffs_e1 else -1) <= 0 or hi <= 0,
            },
            "E2_no_mcs_advantage": {
                "dMCS_sacm_vs_naive": round(dMCS_n, 4),
                "rule_hit": dMCS_n <= 0,
            },
            "E3_retention_tradeoff": {
                "dTSR_retention_sacm_vs_naive": round(dTSR_ret, 4),
                "retention_tolerance": RETENTION_TOLERANCE,
                "rule_hit": dMCS_n > 0 and dTSR_ret < RETENTION_TOLERANCE,
            },
            "E4_context_confound": {
                "dMCS_sacm_vs_full": round(dMCS_full, 4),
                "mme": MME,
                "rule_hit": abs(dMCS_full) <= MME,
            },
            "E5_misattribution": _failure_shift(by_sys.get("sacam_v0", []), by_sys.get("naive_retrieval", [])) if
            "naive_retrieval" in by_sys else {},
        }

    any_rule = [k for k, v in e_rules.items() if "rule_hit" in v and v["rule_hit"]]
    evidence_row = {
        "phase": cfg.phase,
        "evidence_applies": cfg.phase == "full",
        "not_supported": any(bool(x) for x in any_rule),
        "hit_rules": any_rule,
        "n_rules_evaluated": len(e_rules),
    }

    out = {
        "experiment_id": exp_id,
        "config_hash": cfg.hash(),
        "benchmark_hash": file_sha256(ROOT / "benchmark" / "v0" / "tasks.jsonl"),
        "phase": cfg.phase,
        "metrics": tables,
        "e_rules": e_rules,
        "evidence": evidence_row,
    }

    out_dir = ROOT / cfg.results_dir / "processed" / exp_id
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "tables.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    _write_report(out_dir / "report.md", out)
    print(f"Analysis written to {out_dir}")


def _write_report(path: Path, out: dict) -> None:
    lines = [
        f"# Analysis — {out['experiment_id']}",
        "",
        f"- phase: `{out['phase']}`",
        f"- config hash: `{out['config_hash']}`",
        f"- benchmark hash: `{out['benchmark_hash']}`",
        "",
        "## TSR (primary metric)",
        "",
        "| system | n | mean | stdev | min | max | MCS | TSR(ret) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s, m in out["metrics"].items():
        t = m["tsr"]
        lines.append(
            f"| {s} | {m['n_cells']} | {t['mean']:.3f} | {t['stdev']:.3f} | "
            f"{t['min']:.3f} | {t['max']:.3f} | {m['mcs']:.3f} | {m['tsr_retention']:.3f} |"
        )
    lines += ["", "## Category success rates", ""]
    first_sys = next(iter(out["metrics"]))
    cats = out["metrics"][first_sys]["by_category"].keys()
    lines.append("| system | " + " | ".join(cats) + " |")
    lines.append("|---|" + "|".join(["---"] * len(cats)) + "|")
    for s, m in out["metrics"].items():
        lines.append("| " + s + " | " + " | ".join(
            f"{m['by_category'].get(c, {}).get('success_rate', 0):.2f}" for c in cats) + " |")
    lines += ["", "## E-rules (evidence-against)", ""]
    applies = "**Applies to this phase:** yes" if out["evidence"]["evidence_applies"] else "**Applies to this phase:** NO — illustrative only (frozen rule targets the full run)."
    lines.append(applies)
    lines.append("")
    for k, v in out["e_rules"].items():
        hit = f"rule_hit={v.get('rule_hit')}" if "rule_hit" in v else ""
        skip = {kk for kk in v if kk not in ("rule_hit", "per_seed_deltas", "label_counts_naive", "label_counts_sacam")}
        lines.append(f"- **{k}** ({hit}): " + "; ".join(f"{kk}={v[kk]}" for kk in sorted(skip)))
    lines.append("")
    lines += [
        "## Harness sanity (smoke phase)",
        "",
        f"- retrieval calls per task (all systems): {sorted({m['retrieval_calls'] for m in out['metrics'].values()})} (must be [1])",
        f"- store growth max: {max(m['store_growth_max'] for m in out['metrics'].values())}",
        f"- memory-section tokens mean: {round(statistics.mean(m['memory_section_tokens_avg'] for m in out['metrics'].values()), 1)}",
        "",
        "> No research claim is derived from smoke-scale runs with a mock reader.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()