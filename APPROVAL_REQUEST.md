# Milestone 1 — Review & Approval Request
# Milestone 2 — Implemented  ·  Milestone 3 smoke run — completed (instrument validation only)

This repository contains **Milestone 1 (specification, approved)** and **Milestone 2
(evaluation harness)**, plus the **Milestone 3 smoke-scale run using the deterministic
mock model**. No research claim exists: the smoke output is instrument validation and is
explicitly not evidence about SACAM. The full live-model benchmark run is unexecuted and
is the only remaining gate before any research statement.

## 1. Deliverables produced (map to the required response format)

| # | Required milestone-1 item | Where it lives | Status |
| --- | --- | --- | --- |
| 1 | Research objective | `docs/research_question.md` §1–2 | Done |
| 2 | Primary research question (formalized) | `docs/research_question.md` §2 | Done |
| 3 | Secondary research questions (adopted/revised/rejected with justification) | `docs/research_question.md` §3 | Done |
| 4 | Hypothesis (explicitly not a fact) | `docs/research_question.md` §4 | Done |
| 5 | Predictions (observable, P1–P5) | `docs/research_question.md` §5 | Done |
| 6 | Evidence against / falsification criteria (E-rule E1–E5) | `docs/research_question.md` §6, `docs/metrics.md` §3 | Done |
| 7 | Alternative explanations (incl. RQ6 confound) | `docs/research_question.md` §7 | Done |
| 8 | Scope and non-goals | `docs/research_question.md` §8 | Done |
| 9 | Benchmark v0 design | `docs/benchmark_specification.md`, `benchmark/v0/SPEC.md` | Done |
| 10 | Task categories (5, operationally disjoint) | `benchmark/v0/SPEC.md` §2 | Done |
| 11 | Task schema (machine-readable + field-by-field) | `benchmark/v0/schema.json`, `docs/benchmark_specification.md` §3 | Done |
| 12 | 3–5 example fixtures (here: 5) | `benchmark/v0/fixtures/*.json` | Done |
| 13 | 30–50 task allocation (here: 40, balanced) | `benchmark/v0/task_manifest.json` | Done |
| 14 | Baselines defined precisely (A–D + control) | `docs/experiment_protocol.md` §1 | Done |
| 15 | Primary metric (TSR, definition/limits) | `docs/metrics.md` §1 | Done |
| 16 | Secondary metrics (each tied to an RQ) | `docs/metrics.md` §2 | Done |
| 17 | Failure taxonomy (operational, frozen priority) | `docs/failure_analysis.md` | Done |
| 18 | Outcome-blind protocol | `docs/experiment_protocol.md` §13, `docs/methodology.md` §5 | Done |
| 19 | Experiment matrix | `docs/experiment_protocol.md` §7 | Done |
| 20 | Confounds and controls | `docs/experiment_protocol.md` §10, `docs/methodology.md` §2 | Done |
| 21 | Proposed repository architecture | `docs/architecture.md` | Done |
| 22 | Milestone 2 implementation plan | this file, §5 | Done |
| 23 | Milestone 3 experiment plan | this file, §6 | Done |
| 24 | Open scientific decisions | this file, §4 | ✅ approved as designed |
| 25 | Acceptance criteria (current status) | this file, §7 | ✅ M2 done; M3 smoke done |

## 2. Executive summary of the design

- **40 deterministic synthetic tasks**, 8 per category (retention, updating,
  stale-conflict, forgetting, adversarial), invented entities only (no model priors).
- **One primary metric** — TSR (task success rate) — with a frozen rule-based predicate;
  secondary metrics only where tied to an adopted RQ.
- **Frozen evidence-against rule (E1–E5)** evaluated only on the full benchmark; MME
  (+0.05) pre-registered as the smallest effect of interest.
- **Four systems + one control** behind a common memory interface; the control
  (Full-Context) isolates the "more context, not better memory" confound.
- The pivotal design choice: **scripted write directives** identical across systems, so
  the benchmark isolates *management*, not the agent's write judgment (see §4 decisions
  1–2).
- Smoke-scale run (Milestone 3) validates the instrument and is explicitly **not**
  evidence.

## 3. What is explicitly NOT claimed

- No experiment has been run. No result exists. No claim about SACAM being better/worse.
- v0 SACAM is a minimal placeholder (read-time management), not the full architecture.
- The smoke run will not be interpreted through the evidence-against rule.

## 4. Decisions — approved as designed (with sign-off recorded)

The requester approved Milestone 1 **as designed**, including **scripted identical
write directives** (decision #1). All ten decisions were adopted and are frozen; the
"If you disagree" column is retained only as the documented fallback for future versions.

| # | Decision | Recommendation | If you disagree |
| --- | --- | --- | --- |
| 1 | **Scripted identical write directives** for all memory systems (isolates management; drops agent write-autonomy from v0.1) | Adopt | → "v0.2-writes" autonomy variant (documented future work) |
| 2 | **No-memory baseline = single-turn isolated context** (a deliberate floor; makes A fail retention/updating but trivially pass forgetting) | Adopt | → full-transcript "infinite context" control as an additional baseline |
| 3 | **Retrieval injected only at query time; no agent tools in v0** | Adopt | → per-event retrieval flag (more realism, more variance) |
| 4 | **Deterministic local term-overlap retrieval** (no embedding API) for reproducibility | Adopt | → specify an external embedding provider + versioning plan |
| 5 | **Memory budget large enough that no eviction occurs in v0** | Adopt | → add an eviction-pressure dimension now |
| 6 | **Structured memory = typed records with key-based reconciliation** (a mild-management baseline by construction; strong comparison) | Adopt | → weaken it (pure key lookup) |
| 7 | **SACAM v0 = minimal read-time management placeholder**; full sleep-consolidation out of scope | Adopt | → specify more SACAM mechanics now (delays milestone) |
| 8 | **MME = +0.05** and retention tolerance = −0.05, pre-registered, configurable-only-by-version | Adopt | → propose a different smallest-effect bound |
| 9 | **Forgetting scored forbid-only** (documented baseline-A-by-ignorance quirk) | Adopt | → require an "awareness" token (less objective) |
| 10 | **Seeds** smoke `{42,7,2024}` / full `{42,7,2024,1337,2718}`; temperature 0; no post-hoc seeds | Adopt | → specify otherwise |

## 5. Milestone 2 implementation plan (on approval)

Incremental build order (each step: files changed → design note → tests → report):

1. repository skeleton + git init
2. benchmark schema (`schema.json`) + validator
3. frozen task generation from `task_manifest.json` → committed `tasks.jsonl`
4. task loader + schema/determinism tests
5. common memory interface
6. no-memory baseline
7. naive-retrieval baseline
8. structured-memory baseline
9. SACAM v0 plugin (minimal read-time management)
10. full-context control condition
11. agent harness + mock & live model adapters
12. evaluator (frozen predicate)
13. failure taxonomy classifier (frozen priority)
14. metrics (TSR + secondary)
15. configuration system + seed handling
16. experiment runner (`experiments/run.py`)
17. structured logging + raw-result storage
18. analysis scripts (tables/figures from raw only)
19. pre-registration manifest (`pre_registration.json`)
20. test suite + end-to-end smoke test (mock model)
21. docs sync + README completion

Constraint: `benchmark/v0/tasks.jsonl` is generated before any run, hashed, and then
treated as immutable.

## 6. Milestone 3 smoke-experiment plan (on approval)

- **Cell:** 8 representative tasks × (4 systems + full_context) × 3 seeds ≈ 15 runs.
- Deliverables: reproduction command; compact results table (per system TSR); per-
  category table; failure analysis of the most common labels; **the strongest observed
  limitation**; reproducibility report (seeds, benchmark hash, config hash, model, env,
  commit, experiment id); explicit "what this demonstrates / does not demonstrate"
  section.
- Smoke output is labeled `instrument_validation`, never evidence.

## 7. Acceptance criteria (current status)

| Criterion | Status |
| --- | --- |
| Research question explicit | ✅ done |
| Hypothesis falsifiable | ✅ done (E1–E5) |
| Benchmark frozen (allocation) | ✅ done (content froze on approval+generation) |
| 30–50 synthetic tasks (40) | ✅ allocation frozen; content generated in M2 |
| Five categories exist | ✅ done |
| Machine-readable schema | ✅ done |
| 3–5 fixtures (5) | ✅ done |
| Baselines precisely defined | ✅ done |
| One primary metric frozen | ✅ done |
| Success/failure rules frozen | ✅ done |
| Failure taxonomy frozen | ✅ done |
| Evidence-against rule exists | ✅ done |
| Evaluation outcome-blind | ✅ done |
| Common interfaces exist | ✅ implemented (M2) |
| Configs reproducible | ✅ done (M2) |
| Seeds controlled | ✅ policy frozen + enforced |
| Raw results preserved | ✅ append-only runner (M2, smoke exercised) |
| Analysis automated | ✅ `experiments/analyze.py` (smoke exercised) |
| Smoke experiment runs | ✅ done (mock model; `sacam_smoke_v01_b5f0e8d9`) |
| Strongest limitation reported | ⏳ gated on full run |
| Tests pass | ✅ 23 passed |
| README reproducible | ✅ commands documented |
| No results fabricated | ✅ (no research results exist; smoke labeled non-evidence) |
| No benchmark choices changed after results | ✅ (freeze policy enforced; `tasks.jsonl` hashed `f78a3491…`) |
| Framework can show SACAM is wrong | ✅ by design (E1–E5, controls) |

## 8. How to approve

Reply (or use the reviewer form) choosing one of:

- **Approve as designed** → I proceed to Milestone 2 (implementing the harness exactly
  per this protocol).
- **Approve with changes** → list the §4 decision(s) you change; the affected docs are
  updated and frozen again before M2.
- **Revisions requested** → I revise the flagged sections and re-present for review.