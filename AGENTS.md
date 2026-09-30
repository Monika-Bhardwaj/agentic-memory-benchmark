# AGENTS.md — project context for coding sessions

OpenCode loads this file at session start. It is the durable resume note for the
SACAM agentic-memory benchmark project. Keep it updated at the END of each session.

## Project status (checkpoint — causal memory evaluation v1)

### SACAM v0.1 (completed)

- **Milestone 1** (scientific spec) — approved & frozen. Docs in `docs/`.
- **Milestone 2** (harness) — complete, committed (`d993d1e`).
- **Milestone 3 smoke** (mock model) — complete; labelled instrument validation.
- **Full live run** — `results/raw/sacam_full_v01_d7149e0b`, gpt-4.1-mini @ temp 0,
  40 tasks × 5 systems × 5 seeds. Hypothesis NOT supported (E1, E2 fire). Review:
  `results/processed/sacam_full_v01_d7149e0b/research_review.md`.
- **v0.2 fix** (`sacam_v1` provenance-aware supersession) — implemented, tested, live
  A/B complete: `sacam_v1_ab_adv_stale_d04df8df`. Adversarial 0.00→0.62; combined
  adv+stale TSR 0.208→0.542 (best); E4 fires; stale_conflict remains the hard axis
  vs structured (0.46 vs 0.88). Review addendum appended to the research review.

### Causal Memory Evaluation v1 (in progress)

- **Protocol v0.1** — FROZEN. `protocol/PROTOCOL_v0.1.md`, `protocol/freeze_record.md`.
- **Benchmark v1** — 80 tasks generated (40 DEV + 40 HELD-OUT), hash `3ab9f940...`.
- **Intervention framework** — Distractor, Stale, Deletion, Counterfactual implemented.
- **Causal estimands** — E1-E5 + CCR implemented.
- **Instrument validation** — DEV run complete with mock model. All systems functional.
- **Protected run** — NOT YET RUN. Requires explicit authorization.

## Key frozen identifiers

### SACAM v0.1
- Benchmark hash (tasks.jsonl): `f78a3491c9ee969d09e862cd89bb648b93df9f8b5c21ca989cd15667d3389367`
- Smoke: `sacam_smoke_v01_b5f0e8d9` · Full: `sacam_full_v01_d7149e0b` · A/B: `sacam_v1_ab_adv_stale_d04df8df`

### Causal Memory Evaluation v1
- Benchmark hash: `3ab9f94052df61bfd56e1619c5013d7eda14d70366c449e9671610946e144639`
- Protocol: `protocol/PROTOCOL_v0.1.md` (FROZEN)
- Freeze record: `protocol/freeze_record.md`
- DEV run: `causal_dev_v1_b3bbae92` (instrument validation only)

## How to run (from repo root)

### SACAM v0.1 (legacy)
```bash
python -m pytest tests -q                                    # 25 tests
python experiments/run.py --config configs/smoke.yaml        # smoke (mock, fast)
python experiments/analyze.py --config configs/smoke.yaml    # smoke report
python experiments/run.py --config configs/benchmark_v0.yaml # full live (1000 cells)
python experiments/analyze.py --config configs/benchmark_v0.yaml
python experiments/run.py --config configs/sacam_v1_ab.yaml  # v0.2 A/B (240 cells)
python experiments/analyze.py --config configs/sacam_v1_ab.yaml --primary sacam_v1
```

### Causal Memory Evaluation v1
```bash
python -m pytest tests -q                                    # 64 tests (25 v0 + 39 v1)
python experiments/generate_v1_benchmark.py                   # regenerate v1 tasks
python experiments/run_causal.py --config configs/causal_dev.yaml      # DEV run (mock)
python experiments/analyze_causal.py --config configs/causal_dev.yaml  # DEV analysis
# PROTECTED RUN REQUIRES EXPLICIT AUTHORIZATION:
# python experiments/run_causal.py --config configs/causal_protected.yaml
```

Live model needs `.env` (gitignored): `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
Mock = `model.name: mock_pattern_reader` (no keys needed).

## Non-negotiable rules (from research integrity contract)

- `benchmark/v0/tasks.jsonl` is FROZEN. Any change = new minor version (v0.2+), never a silent edit.
- `benchmark/v1/tasks.jsonl` is FROZEN. Any change = new minor version (v1.1+), never a silent edit.
- No fabricated results. Absent results are marked absent.
- `results/` is git-ignored (regenerable from frozen artifacts + config + model + seeds).
  `.env` is git-ignored; never commit or log the API key.
- E-rules are evaluated only on the full run (subset A/B verdicts are directional only).
- SACAM v0/v1 results say nothing about the full sleep-consolidation architecture.
- **Causal evaluation v1: Protected run requires explicit authorization.**
- **Causal evaluation v1: HELD-OUT tasks must not be used for tuning.**
- **Causal evaluation v1: Negative and inconclusive results must be preserved.**

## Citations and contributions

### Reused from SACAM v0.1
- Memory interface design (`src/memory/base.py`)
- Term-overlap retrieval (`src/utils/retrieval.py`)
- Failure taxonomy framework (`src/evaluation/classifier.py`)
- Evaluator (`src/evaluation/evaluator.py`)
- Config system (`src/config/__init__.py`)

### New in causal memory evaluation v1
- Counterfactual intervention layer (`src/interventions/counterfactual.py`)
- Causal estimands framework (`src/causal/estimands.py`)
- Counterfactual consistency rate (`src/causal/consistency.py`)
- Multimodal observation interface (`src/multimodal/observation.py`)
- Procedural scene generator (`src/multimodal/scene_generator.py`)
- Intervention framework (`src/interventions/`)

## Next steps (suggested for the resuming session)

1. **Complete remaining implementation** for causal memory evaluation v1.
2. **Run protected experiment** with explicit authorization (live model required).
3. **Generate protected analysis** with causal estimands and CCR.
4. **Write research review** with negative/inconclusive findings.
5. **Identify strongest limitation** of the causal evaluation.
6. **Consider extensions**: multi-model replication, larger task sets, additional interventions.
