# Research Question Specification

This document formalizes the research questions, hypothesis, predictions, and
falsification criteria for SACAM. It is part of the **frozen Milestone 1 protocol**:
once approved and experiments begin, none of the decision rules below may change
without creating a new benchmark version.

## 1. Problem context

Agentic LLM systems that operate across many interactions need some way to carry
information forward. The naive approach is a persistent store: append everything,
retrieve top-k by similarity, inject into context. An alternative family of designs
actively **manages** memory: what to retain, what to update, what to forget, what to
consolidate, how to resolve conflicts, and how to treat untrusted or adversarial input.

The research program ("SACAM") proposes such active management. This document does
**not** assume the proposal is correct. Its purpose is to make the claim precise,
falsifiable, and measurable.

## 2. Primary research question

> **RQ1.** Does an agentic-memory system with explicit memory management provide
> measurable improvement over (a) no persistent memory and (b) naive persistent
> retrieval, on long-horizon tasks involving correct retention, memory updating,
> stale-memory conflicts, explicit forgetting, and misleading/adversarial memory?

Three nested comparisons are implied by RQ1:

- **C1 (memory vs none):** naive retrieval vs no-memory — does persistence help at all?
- **C2 (management vs retrieval):** SACAM vs naive retrieval — does *active management*
  help beyond naive persistence?
- **C3 (structure vs retrieval):** structured memory vs naive retrieval — does
  representation structure alone help?

RQ1 is only fully answered if C1, C2, and C3 are distinguished. The benchmark is
designed so that C2 is the central comparison and C3 is a diagnostic decomposition.

**Operationalization.** "Long-horizon" is operationalized as *scripted sessions*
(e.g., >= 4 interactions) in which information required at the final query was
introduced earlier under controlled distractor load (see `benchmark/v0/SPEC.md`).
"Involves X" means the frozen event stream contains the corresponding memory behavior
(retention, update, conflict, forgetting, injection) as a first-class operation.

## 3. Secondary research questions

Each secondary question is assessed below, then **adopted, revised, or rejected**.
This assessment is frozen.

| # | Question as proposed | Assessment | Decision |
| --- | --- | --- | --- |
| RQ2 | Does memory improve long-horizon performance relative to no persistent memory? | Subsumed by C1; well operationalized given a *defined* no-memory condition. | **Adopted** (as C1). |
| RQ3 | Does structured memory outperform naive retrieval memory? | Operationalizable; requires precise "structured" definition (provided). Risk: structure versus information-content confound; the full-context control addresses the latter. | **Adopted** (as C3). |
| RQ4 | Does active memory management reduce stale-memory failures? | Operationalizable via category success rate and taxonomy label `STALE_MEMORY_FAILURE`. Requires distinguishing inflow-of-new-info (update) from active conflict (stale). | **Adopted**, with the update/stale distinction made explicit (see §5 and SPEC). |
| RQ5 | Does explicit forgetting reduce interference from obsolete information? | **Rejected as stated** — "interference from obsolete information" conflates forgetting with stale-conflict resolution, and "interference" is not directly observable in the final answer without a causal probe. | **Revised** to: *Does explicit forgetting (a store-level removal directive) prevent re-use of the forgotten information at query time, as measured by the forgetting-category success rate and `FORGETTING_FAILURE` rate?* |
| RQ6 | Is any improvement caused by better memory management, or merely by providing additional retrieved context? | The single most important confound. Cannot be answered by the naive vs SACAM comparison alone. | **Adopted** as the **context-confound control** — a dedicated experimental condition (Full-Context control) plus a token-overhead diagnostic (see `docs/experiment_protocol.md` §Confounds). |
| RQ7 | Which task categories expose weaknesses in each memory architecture? | Operationalizable via category-level success rates and failure-category rates. | **Adopted**, as a descriptive/diagnostic question. |
| RQ8 | Under adversarial/misleading memory injection, does sophisticated memory management remain reliable? | Operationalizable via the adversarial category. Requires provenance to be visibly represented in context but the `adversarial` flag to remain **hidden from the model** (see SPEC). | **Adopted**. |

## 4. Hypothesis

> **H.** A memory system that explicitly manages what should be retained, updated,
> forgotten, and consolidated produces measurably better task outcomes than a naive
> persistent-retrieval system, specifically where old, conflicting, obsolete, or
> misleading memories compete, and does not worsen outcomes for plain correct retention.

**Scope of H, explicitly.** H is about *read- and store-time management of a memory
store*, under the controlled protocol where write directives are deterministic and
identical across systems. H is **not** (in v0.1) about: end-to-end agent autonomy in
deciding what to write, cross-model generalization, or the full "sleep-consolidation"
architecture, which is future work (§8).

**H is a hypothesis, not a fact.** The benchmark must be capable of refuting it.

## 5. Predictions

If H is correct, the following observations should hold in the **full benchmark** run
(definitions of the composite scores are in `docs/metrics.md`; the decision rule and
its scope in `docs/experiment_protocol.md`):

1. **P1 — Management advantage:** SACAM > naive retrieval on the *management-critical
   score* (mean of the updating, stale-conflict, forgetting, and adversarial categories),
   beyond the pre-registered minimal meaningful effect (default effect size and rule:
   see `docs/metrics.md`, `MME`).
2. **P2 — No retention trade-off:** SACAM on the retention category is not worse than
   naive retrieval beyond a pre-registered tolerance (default −0.05 absolute TSR).
3. **P3 — Structure is not sufficient:** C3 shows structured memory alone does not
   fully account for the SACAM advantage (i.e., SACAM > structured on management-critical
   categories by more than measurement noise and beyond MME) — otherwise the "management"
   attribution is disconfirmed in favor of "representation structure".
4. **P4 — Context-confound control:** SACAM's advantage over naive retrieval on
   management-critical categories persists when compared against the Full-Context
   control (naive retrieval with top-K = store size). If SACAM ≈ Full-Context control,
   the advantage is attributable to *information availability*, not management (see §7).
5. **P5 — Failure-pattern signature:** the SACAM advantage arises as a reduced
   `STALE_MEMORY_FAILURE`, `FORGETTING_FAILURE`, and `ADVERSARIAL_MEMORY_FAILURE` rate,
   not merely as fewer `REASONING_FAILURE` labels (the latter would indicate the benefit
   is generic context quality, not memory management).

Predictions P1–P5 are jointly required for H to be considered supported. This is the
pre-registered falsification frame; the smoke-scale run cannot exercise it (see §6-E).

## 6. Evidence against (falsification criteria)

An explicit, pre-registered **evidence-against rule** (E-rule). Notation and effect
definitions are in `docs/metrics.md`. The rule is *symmetric*: it does not require SACAM
to be strong, it requires the experiment to be able to detect *that SACAM is not* strong.

### E-rule (applies to the full benchmark run, not the smoke run)

The hypothesis H is considered **not supported** if **any** of the following is true:

- **E1 (direction):** median over seeds of (SACAM − naive retrieval) on the primary
  metric is ≤ 0, or, for the full run with adequate power, the bootstrap 95% confidence
  interval for that difference has upper bound ≤ 0.
- **E2 (no management-critical advantage):** SACAM is not strictly above naive retrieval
  on the management-critical score, i.e., active management shows no advantage exactly
  where it is posited to matter.
- **E3 (retention trade-off):** SACAM's management-critical advantage is accompanied by
  a retention drop below the pre-registered tolerance (−0.05 absolute), indicating the
  system fixed stale/adversarial failures only by sacrificing correct retention.
- **E4 (context confound):** SACAM ≈ Full-Context control on management-critical
  categories (difference ≤ MME and CI overlapping), i.e., the apparent benefit is
  consistent with "more information made available" rather than "better management".
- **E5 (mis-attribution):** P5 fails — the advantage is carried by fewer
  `REASONING_FAILURE` labels rather than reduced stale/forgetting/adversarial labels.

### Inconclusive evidence

The outcome is classified **inconclusive** (not "support") when the data cannot
distinguish competing explanations, including:

- The sample (tasks × seeds) is too small for the pre-registered effect size to be
  detectable (state this explicitly; do not upgrade to "supported").
- The Full-Context control is neither clearly worse nor clearly equal to SACAM.
- Only a subset of categories is favorable while others are unresolved.
- Model/provider nondeterminism produces wide confidence intervals relative to MME.

### Evidence threshold definition (MME)

The **minimal meaningful effect (MME)** default is **+0.05 absolute** on the relevant
success-rate measure. It is a pre-registered *smallest effect of interest*: below this
magnitude, even if real, a benefit on this benchmark is unlikely to translate into
agentic practice, given that active management adds computational complexity and
engineering risk. MME is a config value (`evidence.mme`) frozen at registration; it is
**not** tuned to make SACAM look good.

> The smoke experiment (Milestone 3) does **not** decide any part of the E-rule.
> It validates the instrument. This is stated here, now, before any result.

## 7. Alternative explanations

If an observed SACAM advantage exists, these must be investigated — they are first-class
controls in the protocol, not afterthoughts:

1. **More information, not better management (the primary confound; RQ6/C4).** SACAM may
   simply place *more useful text* in the prompt. Control: Full-Context condition + token
   overhead diagnostic + P4. A designed "same-items-different-management" ablation is
   future work (see `docs/benchmark_specification.md` §Future work).
2. **Representation structure, not management.** Structured records may be easier for an
   LLM to read than flat sentences; this is an alternative mechanism for any advantage,
   even if P4 passes. Addressed by C3/P3.
3. **Prompt-shape effects.** The rendered format of the memory section (§Renderer in
   `docs/experiment_protocol.md`) differs between systems; a rendering that accidentally
   places the correct item higher, or adds meta-annotations, could explain gains.
   Mitigation: pinned shared renderer, identical structure across systems where possible,
   and recording the *exact* rendered prompt to the raw log for post-hoc inspection.
4. **Retrieval luck on v0 tasks.** v0 uses term-overlap deterministic retrieval; on
   small synthetic corpora the naive matcher may behave favorably or unfavorably. This
   is not controlled away; it is *reported* (embedding/retrieval logs are raw-preserved).
5. **Evaluation leakage into prompts.** Covered by the contamination-control guarantees
   (synthetic invented entities, no task text in the system prompt, frozen evaluator).
6. **Model prior leakage.** Invented facts (e.g., fictitious product/entity names) are
   used precisely so the LLM cannot know answers from pretraining priors.

## 8. Scope and non-goals

### In scope (v0.1)

- Deterministic, synthetic, frozen benchmark of 40 tasks, five categories.
- Stored behavior and read-time behavior of memory systems behind a **common interface**.
- Scripted, identical write directives across systems (isolates management mechanism).
- Four systems + one full-context control condition.
- Rule-based objective evaluation (primary metric TSR), pre-registered statistics.
- Instrument validation via a smoke-scale run.

### Explicitly out of scope (v0.1)

- **Agent-autonomous write policies** (agent deciding *what* to store) — this is a
  designed future variant (`benchmark_v0.2-writes`), because it conflates the agent's
  judgment with the memory system's management.
- **Full sleep-consolidation SACAM architecture.** v0 SACAM is only the minimal
  pluggable placeholder (see `docs/benchmark_specification.md` §SACAM v0), so results
  cannot be read as evidence about the full architecture.
- **Eviction under storage pressure.** Memory budget is sized so no eviction occurs;
  pressure-induced forgetting is a future benchmark dimension.
- **Cross-model generalization claims.** One model per run, documented; generalizing
  across models is future work.
- **Publication-grade statistical power.** The full benchmark is designed for
  preliminary evidence and honest effect sizes, not to power a final paper alone.
- **Human annotation, private data, web search, proprietary benchmarks.**

## 9. Non-negotiable integrity rules (repeat of specs; enforced)

1. Benchmark, metrics, and decision rule freeze before results are inspected.
2. No tuning of any system ("SACAM" included) against the frozen evaluation set.
3. Raw per-run outputs preserved; no overwriting; no withheld seeds.
4. Smoke results are instrument validation, never claims about H.
5. Inconclusive results are reported as inconclusive.

## 10. Status

- [x] Research question formalized
- [x] Secondary questions assessed and adopted/revised/rejected
- [x] Hypothesis, predictions, falsification criteria defined
- [x] Alternative explanations identified and mapped to controls
- [x] Scope and non-goals fixed
- [ ] Approved by research owner (pending)
- [ ] Frozen in pre-registration manifest (Milestone 2, upon approval)