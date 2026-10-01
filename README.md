# SACAM — Agentic-Memory Benchmark & Causal Memory Evaluation

**Status:** 
- **SACAM v0.1** (legacy): Complete. Full live run executed. Hypothesis NOT supported (E1, E2 fire).
- **Causal Memory Evaluation v1** (current): Protocol frozen. Benchmark generated. Instrument validation complete. Protected run pending explicit authorization.

This repository is an **experimental instrument**, not a demonstration. Its purpose is to
determine whether persistent memory causally improves multimodal reasoning under controlled
interventions — and, critically, to be capable of producing evidence **against** that claim.

> Nothing in this repository is a research result. The smoke-scale and development runs
> with the mock model validate the *instrument*, not the hypothesis.

---

## Overview

Agentic LLM systems increasingly rely on persistent memory to behave coherently across
many interactions. The **causal memory evaluation** asks a deeper question than "does memory help?":

> **What is the causal effect of persistent memory on multimodal reasoning performance under controlled memory interventions?**

The key innovation is the **counterfactual intervention layer**: paired conditions where
everything is identical except memory state, allowing us to measure whether controlled
changes in memory state produce predictable changes in downstream behavior.

## Research question

> When an agent receives multimodal observations over multiple steps, does persistent memory
> improve reasoning on later tasks compared with no memory and retrieval-only memory, and can
> controlled interventions demonstrate that the improvement is attributable to memory rather
> than additional context, retrieval, compute, or other confounds?

Full protocol specification: [`protocol/PROTOCOL_v0.2.md`](protocol/PROTOCOL_v0.2.md).

## Hypotheses

- **H1:** Persistent memory improves multimodal reasoning
- **H2:** Retrieval alone explains most of the benefit
- **H3:** Memory management provides additional benefit
- **H4:** Memory can introduce harmful interference
- **H5:** Memory interventions have causal effects

## Benchmark v1

80 deterministic synthetic multimodal tasks across 7 categories:
- Retention (12), Updating (12), Stale conflict (12), Forgetting (12)
- Adversarial (12), Counterfactual (10), Distractor (10)

Split: 40 DEV + 40 HELD-OUT. Hash: `3ab9f94052df61bfd56e1619c5013d7eda14d70366c449e9671610946e144639`

Specification: [`benchmark/v1/schema.json`](benchmark/v1/schema.json)

## Systems

| ID | System | Description |
|----|--------|-------------|
| A | no_memory | No persistent memory |
| B | naive_retrieval | Append + top-k retrieval |
| C | structured_memory | Typed records, key-based reconciliation |
| D | sacam_v1 | Proposed: provenance-aware management |
| E | full_context | Control: retrieval with top_k = all |

## Causal estimands

| Estimand | Comparison |
|----------|-----------|
| τ_memory | memory vs no memory |
| τ_retrieval | retrieval-only vs no memory |
| τ_management | proposed vs retrieval-only |
| τ_intervention | memory state A vs B |
| CCR | counterfactual consistency rate |

## Key metrics

- **Primary:** Task Success Rate (TSR)
- **Secondary:** MCS, category success rates, CCR, failure rates, retrieval quality

## Protocol freeze

The protocol is **frozen** at v0.2. See [`protocol/freeze_record.md`](protocol/freeze_record.md).

## How to run

### One-command entry point
```bash
make test          # Run all tests (64 tests: 25 v0 + 39 v1)
make dev           # Run development experiment (mock model, no API)
make dev-analysis  # Run development analysis
make generate      # Regenerate benchmark v1 tasks
make protected     # Run protected experiment (REQUIRES AUTHORIZATION)
```

### Individual commands
```bash
python -m pytest tests -q                                    # 64 tests (25 v0 + 39 v1)
python experiments/run_causal.py --config configs/causal_dev.yaml      # DEV run (mock)
python experiments/analyze_causal.py --config configs/causal_dev.yaml  # DEV analysis
# PROTECTED RUN REQUIRES EXPLICIT AUTHORIZATION:
# python experiments/run_causal.py --config configs/causal_protected.yaml
```

## Repository structure

```
agentic-memory-benchmark/
├── protocol/                    # Frozen protocol specification
│   ├── PROTOCOL_v0.1.md
│   ├── IMPLEMENTATION_PLAN.md
│   └── freeze_record.md
├── benchmark/
│   ├── v0/                      # SACAM v0.1 (legacy, frozen)
│   └── v1/                      # Causal memory evaluation v1
│       ├── schema.json
│       ├── task_manifest.json
│       └── tasks.jsonl
├── src/
│   ├── multimodal/              # Multimodal observation interface
│   ├── interventions/           # Intervention framework
│   ├── causal/                  # Causal estimands and consistency
│   ├── memory/                  # Memory systems (v0 + v1)
│   ├── agents/                  # Agent harness and models
│   ├── evaluation/              # Evaluator and classifier
│   └── tasks/                   # Task loaders and generators
├── experiments/                 # Experiment runners and analysis
├── configs/                     # Experiment configurations
├── tests/                       # Test suite
├── logs/                        # Experiment log
└── docs/                        # Documentation (v0.1)
```

## Citations and contributions

### Reused from SACAM v0.1
- Memory interface design, term-overlap retrieval, failure taxonomy, evaluator, config system

### New in causal memory evaluation v1
- Counterfactual intervention layer, causal estimands framework, CCR metric
- Multimodal observation interface, procedural scene generator
- Intervention framework (distractor, stale, deletion, counterfactual)

## Non-negotiable rules

- `benchmark/v0/tasks.jsonl` and `benchmark/v1/tasks.jsonl` are FROZEN
- No fabricated results
- Protected run requires explicit authorization
- HELD-OUT tasks must not be used for tuning
- Negative and inconclusive results must be preserved
- No private data
- No unauthorized paid compute/API

## License

MIT
