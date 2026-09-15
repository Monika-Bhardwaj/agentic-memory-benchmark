# SACAM — Agentic-Memory Benchmark & Evaluation Instrument

**Status:** Milestone 1 (specification) and Milestone 2 (evaluation harness) complete;
Milestone 3 smoke-scale run executed with the deterministic mock model as **instrument
validation only** (no research claims). The full live-model benchmark run is the only
remaining gate before any research statement is possible.

This repository is an **experimental instrument**, not a demonstration. Its purpose is to
determine whether a memory system with explicit memory management ("SACAM") measurably
improves long-horizon agentic-task performance over the baselines defined here — and,
critically, to be capable of producing evidence **against** that claim.

> Nothing in this repository is a research result. The smoke-scale run with the mock
> model validates the *instrument*, not the hypothesis.
> No milestone-1 decisions may change after experiments begin.

---

## Overview

Agentic LLM systems increasingly rely on persistent memory to behave coherently across
many interactions. It is an open question whether *actively managing* memory — deciding
what to retain, update, forget, consolidate — is measurably better than naive persistent
retrieval. SACAM proposes mechanisms (selective retention, updating, explicit forgetting,
consolidation, stale-memory resolution). This project builds a **frozen, deterministic,
synthetic benchmark** plus a **reproducible evaluation harness** that can produce evidence
for, against, or inconclusive about that proposal.

## Research question

> Does an agentic-memory system with explicit memory management provide measurable
> improvement over no-memory and naive persistent retrieval baselines on long-horizon
> tasks involving retention, updating, stale information, forgetting, and misleading memory?

Full formalization, secondary questions, hypotheses, predictions and falsification rules:
[`docs/research_question.md`](docs/research_question.md).

## Hypothesis (clearly not established)

> Explicit memory management yields measurably better outcomes than naive persistent
> retrieval on the frozen benchmark — specifically on categories that require resolving
> stale, obsolete, or misleading memories — without degrading correct retention.

This is a falsifiable hypothesis, not a claim.

## Benchmark

Benchmark v0.1: 40 deterministic synthetic tasks across five categories
(retention, updating, stale-conflict, forgetting, adversarial). Specification:
[`benchmark/v0/SPEC.md`](benchmark/v0/SPEC.md). Frozen task allocation:
[`benchmark/v0/task_manifest.json`](benchmark/v0/task_manifest.json).

## Baselines

| System | Definition |
| --- | --- |
| A. No Memory | No persistent memory; single-turn context per interaction. |
| B. Naive Retrieval | Append + deterministic term-overlap retrieval + top-k; no management. |
| C. Structured Memory | Typed records with key-based reconciliation (newest-wins per key); minimal structure. |
| D. SACAM (v0) | Minimal active-management plugin (superseded/untrusted downranking, recency) behind the common interface. Full architecture is future work. |
| Control: Full-Context | Naive retrieval with `top_k = all` (isolates the "more context, not better memory" confound). |

Precise definitions: [`docs/benchmark_specification.md`](docs/benchmark_specification.md).

## Method

Scripted, deterministic interaction sessions with a frozen memory-event stream delivered
identically to every memory system. Evaluation is rule-based, objective, and frozen.
Protocol: [`docs/experiment_protocol.md`](docs/experiment_protocol.md).

## Installation

```powershell
py -3.10 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt        # jsonschema<5, PyYAML<7, pytest<9
pip install -e .                        # optional; tests run from repo root
```

## Quick start

```powershell
python -m pytest tests -q               # 23 tests: tasks, memory, harness, metrics, config
python experiments/generate_benchmark.py # regenerate + validate benchmark/v0/tasks.jsonl (frozen)
python experiments/run.py --config configs/smoke.yaml     # smoke run (mock model, fast)
python experiments/analyze.py --config configs/smoke.yaml # generated report + tables
```

The smoke config runs 8 tasks (2 retention, 2 updating, 2 stale, 1 forgetting,
1 adversarial) × 5 systems × 3 seeds. It uses `mock_pattern_reader`, a deterministic
reader that returns the injected memory section verbatim, so success depends on whether
the right memory was surfaced — it isolates the retrieval/management path.

## Full experiments (live model)

1. Set env vars per `.env.example` (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`).
2. Put the model name into `configs/benchmark_v0.yaml` (`model.name`). Do not change any
   other value — the config hash is part of the raw-result identity.
3. `python experiments/run.py --config configs/benchmark_v0.yaml`
   (40 tasks × 5 systems × 5 seeds; seeds `{42,7,2024,1337,2718}`, temperature 0).
4. `python experiments/analyze.py --config configs/benchmark_v0.yaml`

The E-rule check (E1–E5) is only evaluated on this full run
([`docs/metrics.md`](docs/metrics.md) §3); on the smoke run it is marked *illustrative
only*.

## Evaluation

Primary metric: **Task Success Rate (TSR)** — see [`docs/metrics.md`](docs/metrics.md)
for the exact definition, numerator, denominator, limitations, and the pre-registered
evidence-against rule.

## Results

**No research results exist.** The only executed run is the smoke-scale instrument
validation with the deterministic mock reader (experiment `sacam_smoke_v01_b5f0e8d9`,
report in `results/processed/`). It is labeled `instrument_validation`, never evidence:

| System | TSR (3 seeds) | MCS | TSR retention |
| --- | --- | --- | --- |
| no_memory | 0.125 | 0.167 | 0.000 |
| naive_retrieval | 0.625 | 0.500 | 1.000 |
| structured_memory | 0.875 | 0.833 | 1.000 |
| sacam_v0 | 0.625 | 0.500 | 1.000 |
| full_context | 0.625 | 0.500 | 1.000 |

What the smoke run demonstrates / does not demonstrate:
- **Demonstrates:** generation, validation, harness, evaluator, classifier, metrics,
  analysis and repro artifacts are wired end-to-end and deterministic under the mock.
- **Does not demonstrate:** anything about SACAM, models, or management architectures.

## Limitations

The design's strengths and known limitations are documented before any research result
exists: [`docs/methodology.md`](docs/methodology.md) (including the "more context, not
better memory" confound and baseline-A behavior on forgetting tasks).

## Reproducibility

Every run captures: experiment ID, benchmark version + SHA-256, config hash, seeds, model
identifier/version, prompt version, environment, git commit, timestamp, and raw per-task
outputs. See [`docs/reproducibility.md`](docs/reproducibility.md). Raw artifacts live
under `results/raw/<experiment_id>/<system>_<seed>/` (append-only; `results/` is
git-ignored because it is regenerable from the frozen benchmark + config + model).

## Research integrity

- The benchmark is frozen before any result is inspected (outcome-blind protocol).
- No experimental results may be fabricated; absent results are marked absent.
- No task, metric, or decision rule may change after runs begin; changes create a new version.
- No claim that SACAM "works" may be made unless the experiment demonstrates it.

## Repository layout

```
agentic-memory-benchmark/
├── README.md
├── LICENSE
├── pre_registration.json      (frozen research protocol manifest)
├── pyproject.toml
├── APPROVAL_REQUEST.md        (frozen protocol + M2/M3 status)
├── configs/                   (smoke.yaml, benchmark_v0.yaml)
├── benchmark/v0/              (SPEC, schema, task_manifest, tasks.jsonl, fixtures)
├── docs/                      (research + protocol documents)
├── src/                       (tasks, memory, agents, evaluation, metrics, config, utils)
├── experiments/               (run.py, analyze.py, generate_benchmark.py)
├── tests/                     (23 tests)
└── results/                   (git-ignored; raw/ append-only, processed/ reports)
```