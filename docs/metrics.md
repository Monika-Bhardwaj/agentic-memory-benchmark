# Metrics Specification (Frozen)

Exactly one primary metric; secondary metrics only where they answer a research
question. All names and definitions below freeze with the protocol.

## 1. Primary metric — Task Success Rate (TSR)

### Definition

For a single run (system `S`, seed `r`) over the frozen task set `T` (|T| = N):

```
TSR(S, r) = (1 / N) · Σ_{t∈T} success(t; S, r)
```

where `success(t; S, r) ∈ {0, 1}` is the frozen deterministic predicate
(`task.success_criterion`) applied to the final answer string of task `t`.

Aggregated across seeds:

```
TSR(S) = (1 / R) · Σ_r TSR(S, r)
```

- **Numerator:** number of (task × seed) cells in run $r$ whose final answer satisfies
  the frozen success criterion.
- **Denominator:** number of tasks in the frozen set for run $r$.
- **Aggregation:** per-seed means, then mean across the pre-registered seeds; each run
  level is reported. Bootstrap 95% CI over seeds where the full protocol applies.
- **Interpretation:** the proportion of independent task-sessions the system completes
  correctly. Higher is better; the metric supports baseline-floor amounts if a category
  is unsolvable for a system (reported, never hidden).

### Limitations (stated before results)

- **Binary per task:** no partial credit; a multi-fact answer that is half right fails.
  This is intentional (the primary claim is about completing tasks, not about grading
  partial knowledge) but it discards signal — secondary metrics partially recover it.
- **Single evaluator type:** rule-based substring predicate can miscount answers that are
  semantically right and lexically off-spec. The normalization rule is frozen and
  versioned; manual inspection of a random subset is part of failure analysis.
- **Ceiling effect risk:** if a category is near 0 or 1 for several systems, TSR may not
  discriminate there; category-level rates and failure labels are the diagnostic layer.
- **Not inferential by itself:** TSR is a descriptive rate; uncertainty is expressed via
  per-seed spread and bootstrap CIs, and the evidence-against rule, not by a single test.

### Failure cases (explicit)

A task cell is recorded as failed if: the predicate is false; or the answer is empty /
malformed; or an infrastructure error occurred (label `OTHER`, excluded from TSR but
reported; never silently dropped).

## 2. Secondary metrics

Each is included only because it answers an adopted research question.

| Metric | Definition | Answers | Closely tied to |
| --- | --- | --- | --- |
| Category success rate | TSR restricted to a category (e.g., 8 tasks) | Which categories expose weakness in which architecture (RQ7); per-category falsification inputs (E2, E3) | RQ4, RQ7 |
| Management-critical score (MCS) | Mean TSR over {updating, stale_conflict, forgetting, adversarial} | Does active management help exactly where it is posited to matter (E2/P1) | RQ4, RQ6 |
| Failure-category rate | Count of primary failure labels per category/system per seed (see `docs/failure_analysis.md`) | Where failures originate (store/retrieval/agent); P5 signature | RQ4–RQ8 |
| Retrieval-inclusion rate | Fraction of task cells where `required_item_ids` all appear among the retrieved items at query time | Separates retrieval-side failure from agent-side failure; validates attribution | RQ6 |
| Poison-acceptance rate | Among `adversarial` cells, fraction whose answer contains the injected (false) value | Reliability under injection (RQ8) | RQ8 |
| Memory store growth | Max store size reached per task; items per task | Overhead/engineering cost of management (quantified, not romanticized) | RQ2/C1 |
| Token overhead | Rendered memory-section tokens vs total prompt tokens (query turn) | The information-availability confound (RQ6/P4) | RQ6 |
| Retrieval count per task | Number of retrieval calls (v0.1: exactly 1 by design — sanity check that systems are comparable) | Used as a comparability guard, not a marketing metric | all |

No metric is defined to "make SACAM look good." In particular, no
SACAM-specific metric exists in the frozen set; the closest thing
(`MCS`) is defined over *systems generally*.

## 3. The evidence-against rule (operational)

**Config:** `mme = 0.05`, `retention_tolerance = -0.05` (both frozen defaults, not tuned).

Let `Δ = TSR(SACAM) − TSR(naive_retrieval)` (seed-median of per-seed differences first;
bootstrap CI where the full protocol applies), and `ΔMCS = MCS(SACAM) − MCS(naive)`.

The hypothesis H is **not supported** if **any** of:

- E1: median Δ ≤ 0, or bootstrap upper bound of Δ ≤ 0.
- E2: ΔMCS ≤ 0 (no management-critical advantage).
- E3: ΔMCS > 0 while `TSR(SACAM, retention) − TSR(naive, retention) < retention_tolerance`
  (advantage bought with retention loss).
- E4: `|ΔMCS(SACAM − full_context)| ≤ mme` with overlapping CI (advantage is explained
  by information availability).
- E5: the failure-label shift shows SACAM's gain is dominated by fewer
  `REASONING_FAILURE` labels rather than fewer stale/forgetting/adversarial labels.

**Inconclusive** (never silently called "supported") when: power for `mme` is
insufficient (state N and effect size detected); the full_context control is ambiguous;
or only a subset of categories is favorable.

## 4. Why `mme = 0.05`

It is the smallest effect the benchmark commits to detecting — below it, a benefit is
unlikely to justify management complexity in practice *regardless of statistical
significance*. It is symmetric in spirit: the same MME bounds the oversight of a
SACAM-only advantage and a no-memory advantage; it does not gate which system benefits.

## 5. Anti-gaming notes

- The primary metric is a fixed predicate over a frozen answer contract; models do not
  see the predicate.
- The negation ordering in every secondary metric is frozen (e.g., `STALE_MEMORY_FAILURE`
  fires only on C-category, with new info retrieved; see `docs/failure_analysis.md`), so
  labels cannot be re-defined after runs to flatter or tarnish a system.
- All tables/figures in the repository are generated from raw results;
  nothing is hand-typed into the README.