# Experiment Protocol (Frozen, v0.1)

The complete, pre-registered protocol for executing the SACAM benchmark. Nothing here
may change after runs begin; changes create a new protocol version (tracked alongside
benchmark versions).

## 1. Systems under test

| ID | System | Behavior at a glance |
| --- | --- | --- |
| `no_memory` | A — No persistent memory | No store; no retrieval; agent sees only current event text. Persistence is unavailable by construction. |
| `naive_retrieval` | B — Naive retrieval memory | Append all items; deterministic term-overlap retrieval; top-k injection; literal compliance with update/forget directives; **no** management logic (no recency weighting, no conflict handling, no consolidation). |
| `structured_memory` | C — Structured memory | Items stored as typed records `(entity, attribute, value, source, timestamp, confidence)`; key-based reconciliation: update to a key replaces the single value for that key; conflict on add = newest-wins for the *same key only*. No provenance weighting, no consolidation. |
| `sacam_v0` | D — SACAM (v0 placeholder) | Read-time management minimum: recency weighting + low-confidence/untrusted downweighting + superseded-flag cleanup + key consolidation. Full architecture out of scope. |
| `full_context` | Control — Full-Context | Identical to `naive_retrieval` except top-k = store size (everything surfaced). **Isolates the information-availability confound** (RQ6/P4). |

Design rationale for each baseline is in `docs/benchmark_specification.md` §6 and
`docs/methodology.md`.

## 2. Agent

- A single scripted agent harness executes each task session.
- The agent LLM sees: the shared `scenario` line + each event's rendered text +
  (memory systems only) a **memory section at query time** containing retrieved items.
- The agent's model is identical across systems; the only system-dependent text is the
  shape of the injected memory section (recorded exactly in raw logs).
- v0.1 agent autonomy is limited: it cannot issue memory writes of its own (scripted
  directives only) and cannot call external tools.

### Renderer policy (pinned)

- Memory items render as: `- [id | timestamp | source | confidence] content`.
- The `adversarial` metadata flag is **never** rendered. Provenance is rendered as above.
- System prompts, event rendering, and memory-section rendering are versioned strings
  recorded in the pre-registration manifest.

## 3. Model

- One model (and provider) per experiment; defaults `model.name`, `model.temperature` in
  config.
- `temperature` default **0**. Note in logs that temperature-0 does not guarantee
  bitwise reproducibility across providers; seeds handle rerun variability.
- The tests and smoke-infrastructure runs use a **deterministic mock model**; no live API
  is required to validate the instrument.
- `.env.example` documents `LLM_API_KEY`-style variables; keys are never committed.

## 4. Task environment

- Tasks load from the frozen `benchmark/v0/tasks.jsonl` (version pinned by config).
- Each task = one session; **memory is reset between tasks** (no cross-task leakage).
- Task execution order is the frozen file order, identical for every system.
- Events are shown one per turn. Only the query turn grades the answer (`success
  criterion` predicate on the final answer string).

## 5. Budgets (config defaults, frozen)

| Budget | Default | Meaning |
| --- | --- | --- |
| context | 4096 tokens | Cap on any rendered prompt (watched, logged; exceed → logged warning, task scored OTHER-barring). |
| retrieval | `top_k = 3`; memory-section cap 1500 tokens | Number of items injected and their token ceiling. `full_context` uses top_k = store size. |
| memory | 512 items | Store capacity; **no eviction occurs** in v0.1 tasks (max store ≈ 12 items). |
| inference | 512 output tokens max; 1 attempt per event and per query; no retries | Bounds cost and nondeterminism. |

## 6. Randomization and seeds

- Seeds are pre-registered: **smoke** `{42, 7, 2024}`; **full** `{42, 7, 2024, 1337,
  2718}`. No seeds are added after results exist.
- All deterministic machinery (task variance, retrieval, evaluation) seeds from the run
  seed; table, docs, and logs record them.
- `num_runs` per cell = number of seeds (each run = one system × one seed × all frozen
  tasks).

## 7. Experiment matrix

| System | Retention | Updating | Stale conflict | Forgetting | Adversarial |
| --- | :-: | :-: | :-: | :-: | :-: |
| no_memory | ✓ | ✓ | ✓ | ✓ | ✓ |
| naive_retrieval | ✓ | ✓ | ✓ | ✓ | ✓ |
| structured_memory | ✓ | ✓ | ✓ | ✓ | ✓ |
| sacam_v0 | ✓ | ✓ | ✓ | ✓ | ✓ |
| full_context (control) | ✓ | ✓ | ✓ | ✓ | ✓ |

Every system runs every frozen task. Cells where a category is structurally trivial for
a system are still run and reported (e.g., no_memory on forgetting) — the asymmetry is
documented, not hidden.

## 8. Smoke-scale run (instrument validation only)

Cell: **8 representative tasks** (2 retention, 2 updating, 2 stale, 1 forgetting,
1 adversarial — a diagnostic slice of the frozen manifest) × **4 + control systems** ×
**3 seeds** = 15 runs, ~120 task evaluations with the mock model and a small real-model
confirmation.

Purposes (per the milestone-3 definition):
1. validate task loading, memory interfaces, agent execution, evaluator, metrics,
   logging, reproducibility, failure categorization
2. shake out instrumentation defects
3. produce a **descriptive** results table — explicitly **not** evidence, and never run
   through the evidence-against rule.

## 9. Statistical analysis plan (full benchmark)

- **Reporting:** per-seed TSR per system (table), mean ± SD, per-category rates,
  failure-category rates, token-overhead summary.
- **Inference:** bootstrap 95% CIs (fixed seed for the bootstrap itself, e.g., 3 000
  resamples clustered on runs) for differences of interest: SACAM−naive,
  SACAM−structured, naive−no_memory, SACAM−full_context.
- **Effect sizes:** risk difference (primary) and Cohen's *h* on TSR; report the
  pre-registered MME (+0.05) against any interval estimate.
- **Assumptions:** tasks are the *population* (frozen set), not a sample; inference is
  over runs/seeds and harness randomness, and generalization to unseen future tasks is a
  caveat, not a claim. Avoid parametric tests whose assumptions the small-number-of-seeds
  design does not meet; prefer bootstrap and exact per-seed displays.
- **Explicitly absent:** any per-seed cherry-picking, any post-hoc task removal, any
  significance test added after seeing results.

## 10. Confounds and controls

| Confound | Control / mitigation |
| --- | --- |
| SACAM benefits from *more useful context*, not management (RQ6) | `full_context` condition (P4); token-overhead diagnostic; raw prompt logging. |
| Write-policy differences | Identical scripted directive stream for all systems. |
| Prompt-shape effects | Single pinned renderer; identical structure across systems; exact rendered prompt logged. |
| Embedding/retrieval artefacts | Deterministic term-overlap retrieval, seeded; retrieval logs raw-preserved. |
| LLM nondeterminism | temperature 0 + multiple pre-registered seeds. |
| Order and cross-task leakage | Memory reset per task; frozen task order identical across systems. |
| Model prior leakage | Invented entities; synthetic content; no task text in system prompt. |
| Evaluation leakage | Frozen deterministic predicate; evaluator never sees generator ground truth beyond the frozen criterion. |
| Forgetting task asymmetry (no_memory passes by ignorance) | Documented in `docs/metrics.md` + SPEC; reported per-category, never pooled silently. |

## 11. Data capture per run

Per run (system × seed): rendered transcripts, memory-op log, retrieval log (incl. item
ids surfaced), final answers, per-task success, primary failure label, and metadata (see
`docs/reproducibility.md`). Raw results are append-only.

## 12. Evidence-against rule (summary)

The operational definition of the rule and the MME lives in `docs/metrics.md`; the
research statement in `docs/research_question.md` §6. The rule is only evaluated on the
**full benchmark**, never the smoke run.

## 13. Pre-registration manifest

On approval, `pre_registration.json` is created with: protocol version, benchmark
version + SHA-256, seed lists, config defaults, prompt/renderer versions, MME, E-rule
text, and the approving signature/date. This file is part of the frozen protocol and is
never edited after the first run.