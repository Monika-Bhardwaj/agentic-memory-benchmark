# Benchmark Specification v0.1

Frozen companion to `benchmark/v0/SPEC.md` (the normative, machine-facing spec).
This document explains the design, the task schema, the generation procedure, and
the balance/allocation — at the depth a researcher needs to review and approve it.

## 1. Design principles

1. **Memory behavior, not fact retrieval.** Tasks require the system to behave correctly
   with respect to *what memory did, when, and how it competes* — not merely to look up
   a fact.
2. **Determinism.** Everything downstream of a task's `seed` is deterministic
   (generation, retrieval, evaluation). The only nondeterminism is the LLM sampled at
   temperature 0, over fixed seeds.
3. **Isolation of the "management" variable.** All memory systems receive the *same
   visible interaction script* and the *same frozen memory-directive stream*. The only
   intended difference is how a system represents, stores, retrieves, and manages items
   internally. This is the single most consequential design decision; see §6.
4. **Contamination control.** All facts are about **invented entities** (fictional
   products, teams, rooms, projects) so LLM pretraining priors cannot supply answers;
   no task text appears in the shared system prompt; the evaluator never sees the
   generator's ground truth beyond the frozen criterion.
5. **Outcome blindness.** The task set, metric, and decision rule freeze before any run.

## 2. Task categories

Five categories; every task belongs to exactly one (no composites in v0.1).

| Category | Code | Intent |
| --- | --- | --- |
| Correct retention | `retention` | Info introduced earlier under distractor load must be produced at the final query. |
| Memory updating | `updating` | An existing memory is **authoritatively replaced** (scripted `memory_update` directive). Correct answer follows the new state. |
| Stale-memory conflict | `stale_conflict` | Old memory and newer *conflicting* information both exist; **no authoritative replace directive**. The system must resolve by recency/authority. Distinct from `updating` (see §2.1). |
| Explicit forgetting | `forgetting` | A scripted `memory_forget` directive targets a stored item. The system must stop surfacing/using it. Operational definition in §2.2. |
| Adversarial / misleading injection | `adversarial` | An untrusted, false item is injected with low-confidence provenance; the model opposes it to a trusted item. Distinct from stale (see §2.3). |

### 2.1 `updating` vs `stale_conflict` (operationally disjoint)

- `updating` (B): the script contains a **`memory_update` directive** — an authoritative
  replacement of a specific item id. The correct answer is unambiguously the new value.
- `stale_conflict` (C): the script contains **two conflicting `add` operations** (same
  entity/slot, different values) with **no** update/forget directive. The store legally
  holds both; the correct answer requires the system to resolve toward the more recent /
  more authoritative value. `stale_conflict` measures active conflict resolution;
  `updating` measures obedience to an authoritative change.

### 2.2 Operational definition of "forgetting"

Forgetting is a **store-level and read-time** property; nothing is claimed about LLM
parameters. A forgetting failure means any of:

- the forgotten item **still appears in query-time retrieval results**, or
- the final answer **reproduces the forgotten value**.

Note a consequence (documented as a benchmark limitation): the no-memory baseline cannot
"know" revoked information and therefore trivially passes forbid-only forgetting tasks
by ignorance. The forgetting category therefore primarily discriminates among the memory
systems, **not** between memory and no-memory. This is intentional and reported honestly.

### 2.3 `adversarial` vs `stale_conflict`

- Provenance: adversarial items carry low-confidence / untrusted source metadata, and the
  harness marks them with an `adversarial: true` analysis flag **that is never rendered
  to the model** (the model sees content + source + timestamp + confidence only).
- Truth: the adversarial item's value is *never* the ground truth; a stale item's value
  *was* plausibly correct at some earlier time.
- Expected behavior: prefer the trusted item and, ideally, flag or demote the untrusted
  claim.

## 3. Task schema

The machine-readable schema is normative in `benchmark/v0/schema.json` (JSON Schema
2020-12). Field-by-field semantics:

| Field | Type | Meaning |
| --- | --- | --- |
| `task_id` | string | Unique id, pattern `[A-E]_[A-Z]+_\d{2}` (e.g., `C_STL_04`). Prefix letter = category. Fixtures use `FX` instead of a number. |
| `benchmark_version` | string | `const: "v0.1"` — any change to a task bumps the version, never mutates v0.1. |
| `category` | enum | One of the five categories. |
| `difficulty` | 1/2/3 | Objective rubric, §4. |
| `description` | string | Human-readable summary (inspection aid, never rendered to models). |
| `scenario` | string | Shared world/role line rendered to the model as the session opener. |
| `tags` | string[] | Analysis tags, e.g., `single_fact`, `multi_fact`, `compound`. |
| `events` | event[] | Ordered session script, §3.1. |
| `query` | string | The final question (equivalently, the last event's `text`). Redundant for readability. |
| `distractor_event_ids` | string[] | Event ids that are pure distractors (bookkeeping + diagnostic). |
| `ground_truth` | object | `required_values`[] (must appear), `forbidden_values`[] (must not appear). Values are canonical post-normalization strings. |
| `success_criterion` | object | Frozen, deterministic predicate the evaluator applies to the final answer string (§3.2). |
| `expected_memory_operation` | string | Free-text description of intended memory behavior (inspection aid). |
| `memory_trace` | string[] | Expected store-op sequence, e.g., `["ADD m1","UPDATE m1","FORGET m1"]` — used for instrument validation and mis-trace diagnosis. |
| `required_item_ids` | string[] | Item ids that *must* be present and ideally retrieved at query — the backbone of **automatic failure attribution** (which category failures to which cause). |
| `failure_categories` | failure_label[] | The subset of taxonomy labels that plausibly apply to this task (scopes classification, see `docs/failure_analysis.md`). |
| `seed` | integer | Determinism seed for task generation and any task-local stochasticity. |

### 3.1 Events

| `kind` | Rendered to model | Harness action |
| --- | --- | --- |
| `user_message` | `text` shown | If event carries an `item`, harness issues `memory.add(item)` after showing text (identical for all systems). |
| `memory_update` | `text` shown (if present) | Issue `memory.update(item_id=item.item_id? ...)` — authoritative replace of the targeted item with the event's `item` payload. |
| `memory_forget` | `text` shown (if present) | Issue `memory.forget(item_id)` for the targeted item. |
| `query` | `text` shown | Trigger query-time retrieval (top-k), inject retrieved items, collect final answer. |

Event fields: `event_id`, `kind`, optional `text`, optional `item`
(a `memory_item`: `item_id`, `content`, `metadata{source,timestamp,confidence,adversarial,authority}`),
optional `item_id` (target id for update/forget), optional `note`.

The memory interface and directive semantics are specified in `docs/architecture.md`;
the renderer policy (what the model actually sees) in `docs/experiment_protocol.md`.

### 3.2 Success criterion (deterministic predicate)

`success_criterion` = `{type, values, forbid, normalization, ...}` with:

- `type: "contains_all"` — truthy iff every string in `values` is a substring of the
  normalized final answer, and no string in `forbid` is.
- `normalization`: `lower_strip` (lowercase, strip whitespace/punctuation) or `none`.
- Forbid-only criteria are allowed (`values: []`) — used by forgetting tasks.

The evaluator applies exactly this frozen predicate; no LLM judge, no human judgment in
the primary metric.

## 4. Difficulty rubric (objective, frozen)

| Level | Definition (all three must hold) |
| --- | --- |
| 1 | Query is within **≤ 1 intervening distractor** of the relevant memory event; a **single** fact governs; no competing info. |
| 2 | **2–4 intervening events**; and/or a **single fact + one unrelated info to ignore**; and/or distractors are semantically similar to the queried fact. |
| 3 | **≥ 5 intervening events**; and/or **2+ facts must be combined** to answer; and/or competing or adversarial info is present at query time. |

## 5. Task allocation and balance

**40 tasks, 8 per category**, frozen in `benchmark/v0/task_manifest.json`.

| Category | d1 | d2 | d3 | Total |
| --- | ---:| ---:| ---:| ---:|
| retention | 3 | 3 | 2 | 8 |
| updating | 3 | 3 | 2 | 8 |
| stale_conflict | 3 | 2 | 3 | 8 |
| forgetting | 3 | 3 | 2 | 8 |
| adversarial | 2 | 3 | 3 | 8 |
| **Total** | **14** | **14** | **12** | **40** |

- **Distractor distribution:** each task carries a number of distractor events per its
  difficulty rubric; the manifest records every distractor count.
- **Conflict distribution:** every `updating` (8), `stale_conflict` (8), and
  `adversarial` (8) task involves competing memory by construction; `retention` and
  `forgetting` tasks involve **no** competing add (forgetting involves a competing
  *removal* directive). This keeps the five categories structurally disjoint.
- **Diversity rule:** no two tasks share the same (template, entity-domain) pair; see
  template registry in `benchmark/v0/SPEC.md`.
- **Difficulty spread** ensures the metric has headroom in both directions and avoids a
  floor/ceiling effect that would make a comparison vacuous.

## 6. The "management is isolated" decision (key design choice, needs approval)

The harness delivers a **scripted, frozen memory-directive stream** identical to every
memory system, and renders the same visible script to the agent. Consequences:

- All systems receive identical information-at-input; differences observed at query time
  can only come from **internal representation, retrieval, and management**.
- Trade-off: the agent's *autonomy* in choosing writes is not measured in v0.1. This is a
  deliberate scope decision (documented as the `v0.2-writes` future variant), because
  measuring end-to-end autonomy would conflate (a) the LLM's judgment and (b) the memory
  system's management — defeating the controlled comparison.
- Trade-off for SACAM: its distinguishing behavior in v0.1 lives in *read-time
  management* (recency/resolution weighting, provenance handling, superseded-flag
  cleanup, consolidation of duplicated keys) — **not** in deciding what to write.
  RQ1 is therefore tested v0.1 for the read-time mechanism only. This is stated here,
  before approval, so the researcher can decide whether that is the experiment they want.

### SACAM v0 placeholder (research rationale)

The v0 SACAM system is a **minimal experimental plugin**: behind the common interface it
implements (a) add/update/forget compliance like every system, (b) recency-weighted
retrieval, (c) downweighting of low-confidence/untrusted provenance at read time, and
(d) superseded-flag cleanup. The full consolidation/sleep architecture is **future
research**, explicitly out of scope. Therefore **no v0 result can be read as evidence
for the full SACAM architecture**; it can only be read as evidence about read-time
management.

## 7. Generation procedure (deterministic, reproducible)

1. `task_manifest.json` (frozen): defines 40 rows = {category, id, difficulty, brief,
   seed}. Approved in Milestone 1; content generated in Milestone 2.
2. Generator (`src/tasks/generation/`, created in Milestone 2) expands each row from
   category-specific **templates** + a curated **entity pool** (invented names drawn by
   seeded RNG from a human-readable syllabary — no real trademarks, people, or products).
3. Every generated artifact is written to `benchmark/v0/tasks.jsonl` and **committed**.
   The committed file is the frozen evaluation set; the generator exists for provenance
   and for creating future versions.
4. A `benchmark_hash` (SHA-256 over `tasks.jsonl`) is recorded in the pre-registration
   manifest. Any change → new version (`v0.2...`), never a silent edit.

## 8. Example fixtures

Five complete fixtures (one per category) ship with the specification in
`benchmark/v0/fixtures/`:

| Fixture | Category | What it demonstrates |
| --- | --- | --- |
| `A_RET_FX01.json` | retention | Single fact + 3 distractors; must be retrieved at query. |
| `B_UPD_FX01.json` | updating | Authoritative update directive changes the governing value. |
| `C_STL_FX01.json` | stale_conflict | Two conflicting adds, no directive; must resolve by recency. |
| `D_FGT_FX01.json` | forgetting | Forget directive; the forgotten value must not resurface. |
| `E_ADS_FX01.json` | adversarial | Untrusted injected claim vs trusted claim; must prefer trusted. |

## 9. Versioning policy

- `v0.1` = the version under review in this milestone. Once experiments begin, it is
  frozen forever.
- Any change to tasks, categories, schema, generator, or decision rule creates a new
  version (`v0.2`, ...). Old versions remain committed and loadable.
- The pre-registration manifest records: commit hash, `benchmark_hash`, seed policy,
  config schema hash, and the sign-off.

## 10. Future work (documented, not built now)

- `v0.2-writes`: agent-autonomous write policy variant.
- Memory-pressure/eviction dimension.
- Cross-model generalization runs.
- End-to-end SACAM consolidation architecture.
- "Same items, different management" ablation for the context confound.