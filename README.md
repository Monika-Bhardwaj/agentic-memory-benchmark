# SACAM — Agentic-Memory Benchmark & Evaluation Instrument

**Status:** Milestone 1 (scientific specification) complete. Repository is **NOT yet implemented**.
Awaiting approval before Milestone 2 (repository + evaluation harness) begins.

This repository is an **experimental instrument**, not a demonstration. Its purpose is to
determine whether a memory system with explicit memory management ("SACAM") measurably
improves long-horizon agentic-task performance over the baselines defined here — and,
critically, to be capable of producing evidence **against** that claim.

> Nothing in this repository is a result. No experiments have been run.
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
| B. Naive Retrieval | Append + deterministic embedding + top-k vector retrieval; no management. |
| C. Structured Memory | Typed records with key-based reconciliation; minimal structure. |
| D. SACAM (v0) | Minimal active-management plugin behind the common interface. Full architecture is future work. |

Precise definitions: [`docs/benchmark_specification.md`](docs/benchmark_specification.md).

## Method

Scripted, deterministic interaction sessions with a frozen memory-event stream delivered
identically to every memory system. Evaluation is rule-based, objective, and frozen.
Protocol: [`docs/experiment_protocol.md`](docs/experiment_protocol.md).

## Installation

Pending Milestone 2. No code exists yet.

## Quick start

Pending Milestone 2.

## Full experiments

Smoke experiment, baseline runs, SACAM runs, and analysis commands will be specified
in Milestone 2 after this protocol is approved.

## Evaluation

Primary metric: **Task Success Rate (TSR)** — see [`docs/metrics.md`](docs/metrics.md)
for the exact definition, numerator, denominator, limitations, and the pre-registered
evidence-against rule.

## Results

**No results exist.** This section will only ever contain measured experiment output.

## Limitations

The design's strengths and known limitations are documented before any result exists:
[`docs/methodology.md`](docs/methodology.md) (including the "more context, not better
memory" confound and baseline-A behavior on forgetting tasks).

## Reproducibility

On approval, every run will capture: experiment ID, benchmark version, config hash, seeds,
model identifier/version, prompt version, software environment, git commit, timestamp,
and raw per-task outputs. Policy: [`docs/reproducibility.md`](docs/reproducibility.md).

## Research integrity

- The benchmark is frozen before any result is inspected (outcome-blind protocol).
- No experimental results may be fabricated; absent results are marked absent.
- No task, metric, or decision rule may change after runs begin; changes create a new version.
- No claim that SACAM "works" may be made unless the experiment demonstrates it.

## Repository layout (proposed, pending approval)

```
agentic-memory-benchmark/
├── README.md
├── LICENSE
├── pyproject.toml          (metadata only; no code)
├── APPROVAL_REQUEST.md     (Milestone 1 review checklist)
├── benchmark/v0/           (SPEC, schema, task manifest, fixtures)
├── docs/                   (research + protocol documents)
└── (src/, baselines/, sacam/, configs/, experiments/, results/, tests/)
    → created in Milestone 2 upon approval
```