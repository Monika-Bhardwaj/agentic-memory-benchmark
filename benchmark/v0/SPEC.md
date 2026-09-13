# Benchmark v0.1 — Normative Specification

Frozen specification for the SACAM benchmark **v0.1**. This is the normative companion
to `docs/benchmark_specification.md` (which explains design intent). The terminal files
in this directory (`tasks.jsonl`, produced in Milestone 2) are the frozen evaluation set;
this document is written so that a sibling researcher can re-derive and audit them.

## 1. Version

`benchmark_version: "v0.1"`. Status: proposed (pending milestone-1 approval). After
approval and first run this version is immutable.

## 2. Task categories

Exactly five; each task belongs to exactly one.

| code | category | id prefix | definition |
| --- | --- | --- | --- |
| `R` | retention | `A_RET_xx` | Required info introduced earlier must be produced at the query. |
| `U` | updating | `B_UPD_xx` | An authoritative `memory_update` directive changes the governing value. |
| `S` | stale_conflict | `C_STL_xx` | Conflicting adds for the same entity/slot exist; no directive; resolve by recency/authority. |
| `F` | forgetting | `D_FGT_xx` | A `memory_forget` directive targets an item; it must not resurface or be used. |
| `V` | adversarial | `E_ADS_xx` | Untrusted injected claim vs trusted claim; prefer trusted; `adversarial` flag never rendered. |

## 3. Difficulty rubric (objective)

| level | definition (all must hold) |
| --- | --- |
| 1 | ≤ 1 intervening distractor; single fact; no competing info |
| 2 | 2–4 intervening events, or single fact + unrelated info to ignore, or semantically-similar distractors |
| 3 | ≥ 5 intervening events, or 2+ facts to combine, or competing/adversarial info present at query |

## 4. Schema

Normative: `schema.json` (JSON Schema 2020-12). Key contracts:

- `task_id` pattern `^[A-E]_[A-Z]+_\d{2}$`; fixtures `FX` suffix.
- `events[]` kinds: `user_message` (optional `item` → auto add), `memory_update` (target
  `item_id` + replacement `item`), `memory_forget` (target `item_id`), `query`.
- `memory_item`: `{item_id, content, metadata{source, timestamp:int, confidence:[0,1],
  adversarial:bool, authority:str}}`.
- `success_criterion`: `{type: contains_all, values[], forbid[], normalization}`;
  forbid-only allowed (`values: []`) for forgetting tasks.
- `failure_categories ⊆` the taxonomy labels in `docs/failure_analysis.md`.
- Every task has integer `seed`; the whole file is deterministic given it.

## 5. Task set (frozen allocation)

40 tasks, 8 per category. Frozen allocation lives in `task_manifest.json` (part of this
milestone) and the generated `tasks.jsonl` will be committed and hashed (Milestone 2).

| category | d1 | d2 | d3 | total |
| --- | ---: | ---: | ---: | ---: |
| retention | 3 | 3 | 2 | 8 |
| updating | 3 | 3 | 2 | 8 |
| stale_conflict | 3 | 2 | 3 | 8 |
| forgetting | 3 | 3 | 2 | 8 |
| adversarial | 2 | 3 | 3 | 8 |
| **total** | **14** | **14** | **12** | **40** |

Diversity rules: no two tasks share (template, entity-domain); distractors are drawn from
invented entities; no cross-task content reuse of the same fact.

## 6. Generation procedure

1. `task_manifest.json` rows → category template → seeded RNG sampling from the invented
   entity pool → task object validated against `schema.json`.
2. Generator committed in `src/tasks/generation/` (Milestone 2) for provenance + future
   versions; the **generated file** is the authority.
3. `benchmark_hash` = SHA-256(`tasks.jsonl`) recorded in the pre-registration manifest.

## 7. Contamination controls

- All content synthetic/invented; no real products, people, or private text.
- No task content in the shared system prompt; query text disjoint from generator
  internals; the evaluator applies only the frozen criterion.
- No web search, no external API during retrieval (deterministic local matcher).

## 8. Fixtures

Five complete, human-readable examples in `fixtures/`, one per category, used to review
the task shape before generation of the full set:

- `A_RET_FX01.json` — retention
- `B_UPD_FX01.json` — updating
- `C_STL_FX01.json` — stale_conflict
- `D_FGT_FX01.json` — forgetting
- `E_ADS_FX01.json` — adversarial

## 9. Change policy

Any change to (a) task content/category/difficulty, (b) schema, (c) generation rules,
(d) success criteria, or (e) decision rules after the first run requires a **new
benchmark version** (`v0.2`, ...). Silent edits are prohibited; history is preserved.

## 10. Freeze record

Frozen by the research owner on approval; commit SHA and benchmark hash recorded in
`pre_registration.json` (Milestone 2, before generation).