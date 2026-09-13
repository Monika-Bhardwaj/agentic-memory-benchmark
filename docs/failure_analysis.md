# Failure Analysis Specification (Frozen)

A deterministic failure taxonomy with exact operational definitions and a frozen
classification procedure. Purpose: turn "the agent was wrong" into evidence about
*where the pipeline failed* — store integrity, retrieval, conflict handling, or the
agent's reasoning — without human judgment in the primary path.

## 1. Taxonomy

| Label | Operational definition |
| --- | --- |
| `RETRIEVAL_FAILURE` | At query time the **store no longer contains** a `required_item_id` for this task (i.e., the directive stream should have kept it; the system lost it). Detected from the store state log. |
| `IRRELEVANT_MEMORY_INTERFERENCE` | Required item **is in the store** but is **not in the top-k retrieved set** at query time, while other (irrelevant/competing) items occupy the window. Detected from the retrieval rank log. Pure rank/score interference. |
| `ADVERSARIAL_MEMORY_FAILURE` | Category = `adversarial`, required item retrieved, and the final answer **contains the injected (false) value** or otherwise reflects the poisoned claim. Agent-side adoption of untrusted memory. |
| `FORGETTING_FAILURE` | Category = `forgetting`, and (a) the forgotten item **was retrieved** (still present at read time — store-side failure), **or** (b) the final answer **contains the forgotten value** (agent-side re-use). |
| `STALE_MEMORY_FAILURE` | Category = `stale_conflict`, both conflicting items retrieved, and the final answer reflects the **old/obsolete value** (the value that was once plausible but is now wrong), i.e., conflict resolved toward the wrong pole. |
| `UPDATE_FAILURE` | Category = `updating`, the post-update item retrieved, and the final answer reflects the **pre-update value** — the authoritative replacement was ignored. |
| `REASONING_FAILURE` | All required items were retrieved (or the task has none), yet the final answer is still wrong, and no category-specific label above applies. The available information was present but unused/misused. Pure agent failure. |
| `OTHER` | Infrastructure anomaly: crash, timeout, malformed output, empty response, evaluator error, or any condition violating the run's own invariants. Always reported; never merged into another label. |

## 2. Detection

- Store/retrieval conditions (`RETRIEVAL_FAILURE`, `IRRELEVANT_MEMORY_INTERFERENCE`,
  and the store-side branch of `FORGETTING_FAILURE`) are **automatic** from structured
  logs (store snapshots + retrieval rank per query).
- Answer-content conditions are **automatic** by exact substring checks on the frozen
  forbidden/required values (`ADVERSARIAL_MEMORY_FAILURE`, `FORGETTING_FAILURE` (b),
  `STALE_MEMORY_FAILURE`, `UPDATE_FAILURE`).
- `REASONING_FAILURE` and `OTHER` are automatic by residual and by infrastructure status.

## 3. Classification procedure (frozen priority order)

Each failed task cell receives exactly **one primary label**, assigned by the first rule
below that fires. Analyses may *also* compute co-occurring conditions as documented
secondary annotations, but the primary label is single and deterministic:

1. `OTHER` — infrastructure anomaly occurred.
2. `RETRIEVAL_FAILURE` — required item absent from the store at query time.
3. `IRRELEVANT_MEMORY_INTERFERENCE` — required item in store but outside top-k
   (rank/score problem; memory system's retrieval, not the agent).
4. `ADVERSARIAL_MEMORY_FAILURE` — adversarial value present in answer.
5. `FORGETTING_FAILURE` — forgotten item retrieved, or forgotten value in answer.
6. `STALE_MEMORY_FAILURE` — old value in answer (C-category).
7. `UPDATE_FAILURE` — pre-update value in answer (B-category).
8. `REASONING_FAILURE` — residual wrong answer.

Rationale for the ordering: store/retrieval failures are ranked before agent-side labels
so that a system that fails to *surface* the right item is not mislabeled as a reasoning
failure of the agent; category-specific labels precede the generic residual so that the
tag reflects the task's failure mode rather than a catchall.

## 4. Multiplicity rules

- A cell has exactly one **primary** label (the procedure above).
- A cell may carry secondary annotations for diagnosis, e.g. "poison item was retrieved
  but agent rejected it = *good* adversarial defense, answer still failed for another
  reason" — recorded in the JSONL, never in the primary label.
- Labels apply per task-cell (task × system × seed), never to a whole run; run-level
  summaries are aggregates of cells.

## 5. Failure analysis outputs

For every failed cell, the preserved record (see `docs/reproducibility.md`) must answer:

1. What did the agent observe? (rendered event texts)
2. What memories existed at query time? (store snapshot)
3. What memories were retrieved? (rank log)
4. What memory operations occurred and succeeded? (directive log)
5. What did the agent output? (final answer verbatim)
6. What was expected? (ground truth + fired predicate)
7. What evaluator rule marked it failed? (criterion details)
8. Which failure label fired, and by which branch? (procedure trace)
9. Where did the failure originate (store / retrieval / agent / infra)?

`docs/` companion `failure_analysis.md` canonicalizes the qualitative review template
(sampled manual inspection of a random subset of failures per category, recorded in the
results tree).