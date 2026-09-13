# Methodology

Design philosophy, the pivotal design decisions, their trade-offs, and the honesty
constraints that govern this instrument. This document exists so a skeptical reviewer
can see *why* each choice was made, and what each choice would risk.

## 1. Guiding principle

The only acceptable deliverable is an experiment that can **fail the proposed method**.
Every convenience that would make SACAM succeed is a defect. Every convenience that
would make a baseline fail is a defect. We prefer the stronger test at each fork:

- deterministic over stochastic where comparable
- explicit over hidden configuration
- raw preservation over lossy summaries
- method-agnostic evaluation over method-specific scoring
- a design that could reveal SACAM is wrong, over one that cannot

## 2. The pivotal controls

### 2.1 The information-availability confound (RQ6)

The risk: "SACAM appears better because it gives the LLM more relevant text." Three
controls:

1. **Full-Context condition** — naive retrieval with top-k = store size. If SACAM ≈
   Full-Context, the effect is information, not management (E4). Included in the matrix
   precisely because a naive-vs-SACAM comparison alone cannot answer RQ6.
2. **Token-overhead metric** — the cost of the injected context is measured, so any
   advantage can be judged against its price (the engineering rationale for our MME).
3. **Full transparency of rendered prompts** — the exact prompt is raw-logged so a
   post-hoc reviewer can see whether SACAM simply placed better text in-context.

The *strongest* control (same items, different management, i.e., an ablation) is
documented in `benchmark_specification.md` §10 as future work; it is beyond the
smoke-scale scope and is not over-engineered into v0.1.

### 2.2 Scripted writes vs agent autonomy

We distribute the *same frozen directive stream* to all systems. This is the decision
that most shapes what the experiment can claim:

- **What it preserves:** equivalently-informed systems; the management variable is
  pure; retrieval/read-time behavior is unconfounded with the LLM's write judgment.
- **What it gives up:** the finding cannot claim anything about agents choosing their own
  writes. This is a scope limit, declared in the research question (§8) and in the
  proposal (§6 / §7), not a hidden weakness.

### 2.3 Baseline fairness

Every cell shares: task, task order, visible script, model, temperature, budgets,
seeds, and evaluator. The harness's renderer is the same for every system apart from the
structured memory-section shape. Any remaining differences (e.g., SACAM's annotations in
the memory section) are *log artifacts of the system*, not protocol differences, and are
themselves measured (recording token overhead, exact prompts).

## 3. Why synthetic invented facts

- **Contamination:** invented entities mean the model cannot supply the answer from
  pretraining priors; a correct answer is evidence the system used its memory/injection.
- **Reproducibility:** no external corpora, no web dependencies, no API-varying content.
- **Public + inspectable:** every task is human-readable JSON committed to the repo.

This is the classic way to keep an agentic benchmark *about the mechanism* rather than
about world knowledge.

## 4. What a smoke-scale run can and cannot show

It can: validate every moving part of the instrument end-to-end, sanity-check failure
classification, confirm raw-log sufficiency, and produce a **descriptive** table.

It cannot: produce evidence for or against the hypothesis, run the evidence-against
rule, or make any research claim. We will label smoke outputs accordingly, in README and
in tables (`status: instrument_validation`).

## 5. Outcome blindness in practice

- Freeze everything (this milestone) → approve → create pre-registration manifest
  (commit hash + benchmark hash + config hash + decision rule) → generate frozen task set
  → run → only then inspect.
- The benchmark file `benchmark/v0/tasks.jsonl` (Milestone 2) is committed and hashed;
  the generator is kept only for provenance and future versions.
- Any discovered defect → **new version** (`v0.2`), never a silent tweak to v0.1.

## 6. Known asymmetries and honest accounting

| Asymmetry | Where | How handled |
| --- | --- | --- |
| `no_memory` trivially passes forget-only tasks by ignorance | forgetting category | documented in SPEC + metrics; reported per category, never pooled silently |
| `structured_memory` reconciles same-key adds (mild management by construction) | updating/stale | it is a *stronger* baseline than "naive"; the comparison to it is a diagnostic, not a required win |
| `naive_retrieval` term-overlap matcher may be weak on varied paraphrasing | all | retrieval logs preserved; embedding/retrieval choices are config-visible; a stronger retriever is a future variant, not a silently-swapped v0.1 |
| SACAM v0 is a minimal placeholder, not the full architecture | all | explicitly out of scope; no v0 result speaks to the full architecture |

## 7. Integrity checklist enforced by the instrument

1. No fabricated numbers: results tree only ever contains logged outputs.
2. No concealed seeds, no favorable-seed reporting, no post-hoc seed removal.
3. No tuning on the evaluation set (including prompts and SACAM weights).
4. No metric or rule changes after the first run.
5. Assumptions and measurements are labeled: *assumption*, *config*, *measured*,
   *smoke*, *preliminary*.
6. Inconclusive evidence is reported as inconclusive.