# AGENTS.md — project context for coding sessions

OpenCode loads this file at session start. It is the durable resume note for the
SACAM agentic-memory benchmark project. Keep it updated at the END of each session.

## Project status (checkpoint — v0.2 A/B complete)

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

## Key frozen identifiers

- Benchmark hash (tasks.jsonl): `f78a3491c9ee969d09e862cd89bb648b93df9f8b5c21ca989cd15667d3389367`
- Smoke: `sacam_smoke_v01_b5f0e8d9` · Full: `sacam_full_v01_d7149e0b` · A/B: `sacam_v1_ab_adv_stale_d04df8df`
- Config hashes in `results/processed/*/report.md` headers.

## How to run (from repo root; use the `results/` policy)

```powershell
python -m pytest tests -q                                    # 25 tests
python experiments/run.py --config configs/smoke.yaml        # smoke (mock, fast)
python experiments/analyze.py --config configs/smoke.yaml    # smoke report
python experiments/run.py --config configs/benchmark_v0.yaml # full live (1000 cells)
python experiments/analyze.py --config configs/benchmark_v0.yaml
python experiments/run.py --config configs/sacam_v1_ab.yaml  # v0.2 A/B (240 cells)
python experiments/analyze.py --config configs/sacam_v1_ab.yaml --primary sacam_v1
```

Live model needs `.env` (gitignored): `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`.
Mock = `model.name: mock_pattern_reader` (no keys needed).

## Non-negotiable rules (from research integrity contract)

- `benchmark/v0/tasks.jsonl` is FROZEN. Any change = new minor version (v0.2+), never a silent edit.
- No fabricated results. Absent results are marked absent.
- `results/` is git-ignored (regenerable from frozen artifacts + config + model + seeds).
  `.env` is git-ignored; never commit or log the API key.
- E-rules are evaluated only on the full run (subset A/B verdicts are directional only).
- SACAM v0/v1 results say nothing about the full sleep-consolidation architecture.

## Next steps (suggested for the resuming session)

1. Consider rerun of the FULL benchmark including `sacam_v1` (add to a new config; keep
   `benchmark_v0.yaml` frozen as the v0.1 public record) to re-evaluate E1/E2 with the
   fix at full scale — the A/B was on the adversarial+stale subset only.
2. Decide whether `sacam_v1` becomes the default management plugin or stays a
   comparison row.
3. Implement recommendation set from the review: multi-model × temperature replication,
   larger store pressure / eviction axis, write-autonomy variant, embedding retrieval row.
4. Publish policy: survey the two-axes tension (adversarial vs stale_conflict) — no
   fixed read-time supersession policy wins both; document as a falsifiable design input.