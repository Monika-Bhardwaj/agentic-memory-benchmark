# Causal Memory Evaluation Protocol v0.1

**Status:** DRAFT — pending review and approval  
**Date:** 2026-09-30  
**Supersedes:** SACAM v0.1 benchmark (retains compatible interfaces; extends with causal intervention layer)

---

## A. Research Question

> **What is the causal effect of persistent memory on multimodal reasoning performance under controlled memory interventions?**

More precisely:

> When an agent receives multimodal observations over multiple steps, does persistent memory improve reasoning on later tasks compared with no memory and retrieval-only memory, and can controlled interventions demonstrate that the improvement is attributable to memory rather than additional context, retrieval, compute, or other confounds?

The benchmark is designed to distinguish among five hypotheses (H1–H5) and to produce evidence that can falsify each one.

---

## B. Hypotheses

### H1 — Persistent memory improves multimodal reasoning

Persistent memory improves performance on later multimodal tasks compared with no memory, under matched conditions.

### H2 — Retrieval alone explains most of the benefit

A retrieval-only memory system obtains similar improvements to the proposed memory architecture.

### H3 — Memory management provides additional benefit

The proposed memory system performs differently from retrieval-only memory specifically on tasks requiring updating, conflict resolution, deletion, stale-memory handling, or counterfactual memory changes.

### H4 — Memory can introduce harmful interference

Persistent memory can decrease performance by introducing stale, irrelevant, contradictory, or misleading information.

### H5 — Memory interventions have causal effects

Controlled changes to memory state produce predictable changes in downstream reasoning, while the underlying multimodal evidence and other relevant budgets remain fixed.

---

## C. Predictions

### P1 — Memory advantage over no-memory

If H1 is true: TSR(memory systems) > TSR(no_memory) by more than the pre-registered minimal meaningful effect (MME = +0.05) on at least one category.

### P2 — Management advantage over retrieval-only

If H3 is true: TSR(proposed) > TSR(retrieval_only) on management-critical categories (updating, stale_conflict, forgetting, adversarial) by more than MME.

### P3 — Counterfactual consistency

If H5 is true: When memory state is counterfactually changed from A to B (all else held fixed), the agent's answer changes in the direction predicted by the memory change in ≥ 70% of paired trials.

### P4 — No retention trade-off

If H3 is true without H4 dominating: TSR(proposed, retention) ≥ TSR(retrieval_only, retention) − 0.05.

### P5 — Failure-pattern signature

If H3 is true: The proposed system's advantage arises from reduced STALE_MEMORY_FAILURE, FORGETTING_FAILURE, and ADVERSARIAL_MEMORY_FAILURE rates, not merely from fewer REASONING_FAILURE labels.

---

## D. Alternative Explanations

If the proposed memory system appears to improve multimodal reasoning, the following alternative mechanisms must be investigated:

1. **More information, not better management.** The proposed system may simply place more useful text/images in the prompt. *Control:* Full-Context condition + token-overhead diagnostic.

2. **Representation structure, not management.** Structured records may be easier for the model to read. *Control:* Structured-memory baseline (C3 comparison).

3. **Prompt-shape effects.** The rendered format may differ between systems. *Control:* Pinned shared renderer; exact rendered prompt logged.

4. **Retrieval luck.** Term-overlap retrieval may behave favorably on small corpora. *Control:* Retrieval logs preserved; embedding/retrieval choices are config-visible.

5. **Model prior leakage.** Real-world facts may be known from pretraining. *Control:* Synthetic invented entities; no task text in system prompt.

6. **Evaluation leakage.** The evaluator may leak ground truth. *Control:* Frozen deterministic predicate; evaluator never sees generator internals.

7. **Context budget asymmetry.** Systems may receive different amounts of context. *Control:* Token budgets matched and logged; full_context control.

8. **Multimodal perception differences.** Systems may differ in how they process images. *Control:* Identical image inputs; visual token budgets matched.

---

## E. Causal Estimands

The following estimands are pre-registered. Not all are automatically reported; only those identifiable from the design are claimed.

### E1 — Average memory effect

```
τ_memory = E[Y | memory] − E[Y | no memory]
```

Identified by: random assignment of system (memory vs no-memory) holding task, model, budgets fixed.

### E2 — Retrieval effect

```
τ_retrieval = E[Y | retrieval_only] − E[Y | no memory]
```

Identified by: comparison of retrieval-only vs no-memory under matched conditions.

### E3 — Memory-management effect

```
τ_management = E[Y | proposed] − E[Y | retrieval_only]
```

Identified by: comparison of proposed vs retrieval-only under matched conditions. This is the central estimand.

### E4 — Intervention effect

```
τ_intervention = E[Y | memory_state_A] − E[Y | memory_state_B]
```

Identified by: paired counterfactual conditions where only memory state differs.

### E5 — Category-specific effect

```
τ_category = E[Y | proposed, category=c] − E[Y | retrieval_only, category=c]
```

Identified by: stratified comparison within each task category.

### E6 — Counterfactual consistency rate

```
CCR = P(answer changes in predicted direction | memory state changed)
```

Identified by: paired counterfactual trials with known ground truth.

---

## F. Candidate Multimodal Data Sources

### F.1 Public datasets considered

| Dataset | Source | License | Modality | Suitability | Decision |
|---------|--------|---------|----------|-------------|----------|
| VQA v2 | GQA/COCO | CC-BY-4.0 | Image+Text | Too open-ended; no temporal structure | Rejected |
| OK-VQA | MIT | CC-BY-4.0 | Image+Text | Requires external knowledge; no memory interventions | Rejected |
| A-OKVQA | MIT | CC-BY-4.0 | Image+Text | No temporal memory structure | Rejected |
| ScienceQA | MIT | CC-BY-4.0 | Image+Text | No multi-step memory | Rejected |
| CLEVR | MIT | CC-BY-4.0 | Synthetic Image+Text | Visual reasoning but no memory interventions | Rejected |
| GQA | Stanford | CC-BY-4.0 | Image+Text | Scene graphs but no temporal memory | Rejected |

**Reason for rejection:** None of the existing public multimodal datasets provide the temporal multi-step structure with controlled memory interventions required for causal memory evaluation. They are designed for single-turn visual question answering, not for studying how memory of earlier observations affects later reasoning.

### F.2 Selected approach: Synthetic multimodal benchmark

We design a **procedurally generated synthetic multimodal benchmark** that combines:

1. **Visual scenes:** Procedurally generated images with objects, colors, spatial relationships, and temporal changes.
2. **Textual observations:** Natural language descriptions of visual scenes and factual assertions.
3. **Controlled memory interventions:** Precise manipulation of what enters memory, when, and how it competes.

**Justification:**
- Full control over ground truth (no annotation noise)
- Precise intervention design (impossible with static datasets)
- No contamination from pretraining priors
- Perfect reproducibility
- No licensing concerns
- Can be scaled to required difficulty

**This is not a toy demonstration.** The benchmark is designed to test whether memory mechanisms (retrieval, updating, conflict resolution, deletion) cause predictable changes in reasoning — a scientific question that requires controlled interventions impossible with existing datasets.

---

## G. Synthetic Data Design

### G.1 Visual scene generation

Scenes are procedurally generated with the following elements:

- **Objects:** Geometric shapes (circles, squares, triangles) with attributes (color, size, position)
- **Spatial relationships:** Above, below, left, right, inside, outside
- **Temporal dynamics:** Objects move, change color, appear, disappear across time steps
- **Distractor objects:** Visually salient but task-irrelevant objects

Each scene is rendered as a deterministic image (PNG) with a corresponding textual description.

### G.2 Task structure

Each task consists of a **temporal sequence** of observations:

```
t=1: Observation (image + text) → memory write
t=2: Observation (image + text) → memory write
...
t=k: Distractor observation (image + text) → memory write
...
t=n: Query (text only, or image + text) → retrieval + answer
```

### G.3 Multimodal observation interface

```python
@dataclass
class Observation:
    image: ImageReference  # path or generated image
    text: str               # textual description
    timestamp: int          # temporal order
    metadata: dict          # permitted metadata only (source, confidence)
```

**Ground truth is never included in metadata.**

### G.4 Entity and fact generation

All entities are invented (fictional product names, room names, team names, etc.) to prevent pretraining prior leakage. The entity pool is frozen and versioned.

---

## H. Train/Dev/Held-out Split

### H.1 Split strategy

Since the benchmark is synthetic and procedurally generated, we use a **generation-seed-based split**:

| Split | Purpose | Generation seeds | Task count |
|-------|---------|-----------------|------------|
| DEV | Development, debugging, protocol refinement | 1000–1999 | 40 |
| HELD-OUT | Protected evaluation | 5000–5999 | 80 |

**No TRAIN split** is needed because:
- The benchmark evaluates memory mechanisms, not model capabilities
- All systems use the same model
- No training or fine-tuning occurs
- The task is to measure causal effects of memory interventions, not to train a model

### H.2 Split integrity

- DEV tasks are used for: debugging, smoke tests, protocol refinement, system development
- HELD-OUT tasks are used ONLY for: the protected comparative experiment after protocol approval
- HELD-OUT tasks are never used for: prompt tuning, memory design, intervention design, metric selection, threshold tuning, baseline tuning
- The split is frozen at protocol approval time

### H.3 Task generation

Tasks are generated from frozen templates with seeded RNG. The generation procedure is:

1. Select template (e.g., RET_SINGLE, UPD_LOCATION, STL_CONFLICT, FGT_DELETE, ADS_POISON, CF_COUNTERFACTUAL)
2. Sample entities from frozen entity pool using seed
3. Generate visual scene (if applicable) using seed
4. Generate event sequence with controlled distractor load
5. Validate against schema
6. Assign to split based on seed range

---

## I. Memory Eligibility Rules

### I.1 Allowed into memory

| Information type | Description |
|-----------------|-------------|
| Textual observations | Natural language descriptions of visual scenes |
| Extracted entities | Object labels, colors, spatial relationships |
| Factual assertions | "The red circle is above the blue square" |
| Temporal markers | Order of observations |
| Source metadata | Who/what provided the observation |
| Confidence | Model confidence in the observation |

### I.2 Forbidden from memory

| Information type | Description |
|-----------------|-------------|
| Ground truth labels | Never stored in memory |
| Task metadata | Query text, success criteria |
| Future information | Information from later time steps |
| System identity | Which memory system is being used |
| Evaluation criteria | Success/failure conditions |

### I.3 Write triggers

Memory writes occur when:
1. A `user_message` event carries an `item` → `memory.add(item)`
2. A `memory_update` event → `memory.update(item_id, item)`
3. A `memory_forget` event → `memory.forget(item_id)`

All systems receive the **identical** directive stream.

### I.4 What is stored

```python
@dataclass
class MemoryItem:
    item_id: str
    content: str  # canonical "LABEL: VALUE." form
    metadata: dict  # source, timestamp, confidence, adversarial, authority
```

### I.5 What is retrieved

Retrieval returns a ranked list of `RetrievedItem` objects, each containing the item content, metadata, retrieval score, and rank.

### I.6 What is not accessible

- The no-memory baseline cannot access any stored information
- The retrieval-only baseline can only access retrieved items (top-k)
- The proposed system can access retrieved items plus management metadata
- No system can access ground truth, future information, or evaluation criteria

---

## J. No-Memory Baseline (Baseline A)

### J.1 Definition

The agent has **no persistent memory**. It can access only the information explicitly available in the current interaction.

### J.2 What remains in current context

- The shared scenario/role line
- The current event text (if applicable)
- The query text

### J.3 What is NOT accessible

- Any previously stored information
- Any memory section
- Any retrieved items

### J.4 Implementation

All memory operations are no-ops. Retrieval always returns an empty list.

### J.5 Known asymmetry

The no-memory baseline trivially passes forbid-only forgetting tasks by ignorance. This is documented and reported, not hidden.

---

## K. Retrieval-Only Baseline (Baseline B)

### K.1 Definition

Persistent information can be stored and retrieved using a **deliberately simple** memory architecture.

### K.2 Architecture

```
observation → memory store → retrieval (top-k) → context → model
```

### K.3 Properties

- Append all items as-is
- Deterministic term-overlap retrieval
- Top-k injection at query time
- Literal compliance with update/forget directives
- **No** management logic (no recency weighting, no conflict handling, no consolidation, no provenance weighting)

### K.4 Purpose

To determine whether retrieval itself explains observed gains, or whether active management provides additional benefit.

---

## L. Proposed Memory System

### L.1 Definition

The proposed memory architecture implements **active management** behind the same interface as the baselines.

### L.2 Components

1. **Write policy:** Scripted directives (identical to baselines)
2. **Representation:** Typed records keyed by entity/attribute
3. **Retrieval:** Term-overlap with management weighting
4. **Update:** Authoritative replacement with provenance-aware supersession
5. **Conflict handling:** Recency + authority weighting
6. **Deletion:** Store-level removal with audit trail
7. **Consolidation:** Same-label deduplication with strength comparison

### L.3 Management operations

- **Supersession:** An older same-label claim is marked superseded only when the new claim is not weaker (provenance-aware)
- **Provenance downweighting:** Items with untrusted authority or low confidence are downranked at read time
- **Recency boost:** Mild boost for newer items
- **Conflict resolution:** When conflicting items exist, the system surfaces both but ranks by management policy

### L.4 Scope

The proposed system is a **minimal experimental plugin** implementing read-time and store-time management. The full sleep-consolidation architecture is explicitly out of scope.

---

## M. Matched Budgets

### M.1 Budget table

| Budget | Value | Meaning |
|--------|-------|---------|
| Model calls | 1 per event, 1 per query | No retries in primary metric |
| Context tokens | 4096 | Cap on rendered prompt |
| Retrieval items | top_k = 3 | Number of items injected |
| Memory budget | 512 items | Store capacity (no eviction in practice) |
| Output tokens | 512 | Max tokens per model response |
| Visual tokens | Matched across systems | Same image resolution |
| Temperature | 0 | Deterministic sampling |
| Seeds | Pre-registered | See §Y |

### M.2 Information parity

All systems receive:
- Identical task prompts
- Identical event streams
- Identical model and model version
- Identical temperature and sampling parameters
- Identical token budgets
- Identical image inputs (same resolution, same encoding)

### M.3 Documented differences

| Difference | Justification |
|-----------|---------------|
| Memory section content | This is the independent variable being tested |
| Memory section size | Measured and logged; part of the treatment |
| full_context uses top_k = all | This is the control condition for information availability |

---

## N. Distractor Intervention

### N.1 Design

Introduce irrelevant multimodal information that should not affect the answer.

### N.2 Conditions

| Condition | Description |
|-----------|-------------|
| Control | No distractor; relevant info only |
| Distractor | Relevant info + irrelevant visual/textual distractors |

### N.3 What changes

- Presence of distractor objects in visual scenes
- Presence of distractor facts in event stream

### N.4 What remains fixed

- The relevant information needed to answer the query
- The query itself
- The model and budgets
- The memory system

### N.5 Expected effect

A robust memory system should **not** be affected by distractors. Performance drop indicates:
- Perception failure (distractor confused the model)
- Retrieval failure (distractor crowded out relevant memory)
- Reasoning failure (model was misled by distractor in context)

### N.6 Failure criterion

A distractor-induced failure is **not** automatically a memory failure. It is classified as:
- `DISTRACTOR_INTERFERENCE` if the distractor was retrieved and affected the answer
- `REASONING_FAILURE` if the distractor was in context but the model should have ignored it
- `PERCEPTION_FAILURE` if the distractor confused the visual processing

---

## O. Stale/Conflicting Memory Intervention

### O.1 Design

Create conditions where memory contains information that was once correct but has become outdated.

### O.2 Event sequence

```
t=1: "Object A is at location X" → memory write (m1)
t=2: "Object A is now at location Y" → memory write (m2)
...
t=n: "Where is Object A?" → query
```

### O.3 Conditions

| Condition | Description | Expected answer |
|-----------|-------------|-----------------|
| Updating | Authoritative `memory_update` directive | New value (Y) |
| Stale conflict | Two conflicting adds, no directive | Resolve by recency/authority |

### O.4 What changes

- The memory store contains conflicting information
- The correct answer depends on resolution strategy

### O.5 What remains fixed

- The observations (both are presented)
- The query
- The model and budgets

### O.6 Expected memory operation

- **Updating:** The system should follow the authoritative update directive
- **Stale conflict:** The system should resolve toward the more recent/authoritative value

### O.7 Failure criterion

- `STALE_MEMORY_FAILURE`: The old/obsolete value is in the answer
- `UPDATE_FAILURE`: The pre-update value is in the answer (updating category)
- `CONFLICT_RESOLUTION_FAILURE`: Both values appear without resolution

---

## P. Deletion Intervention

### P.1 Design

Define tasks where information should be removed from persistent memory.

### P.2 Event sequence

```
t=1: "The meeting is at 3pm" → memory write (m1)
t=2: "Forget the meeting time" → memory_forget (m1)
...
t=n: "When is the meeting?" → query
```

### P.3 Operational definition

> Deletion is defined as: the specified information is removed or rendered unavailable through the persistent-memory interface.

**Important:** We do NOT claim that the underlying multimodal model has "forgotten" something if only the external memory store has been modified.

### P.4 Conditions

| Condition | Description |
|-----------|-------------|
| Before deletion | Item is in memory and retrievable |
| Deletion operation | `memory.forget(item_id)` |
| After deletion | Item is removed from store; must not resurface |

### P.5 Expected behavior

- The forgotten item should not appear in retrieval results
- The final answer should not contain the forgotten value
- If the query asks about a different topic, the forgotten item should not interfere

### P.6 Failure condition

- `FORGETTING_FAILURE`: The forgotten item was retrieved, OR the final answer contains the forgotten value

### P.7 Context distinction

The information may still be present in the current context (if the query references it). This distinction is explicit: deletion affects the **memory store**, not the current context.

---

## Q. Counterfactual Intervention

### Q.1 Design

Construct paired conditions where the underlying task is identical, the model is identical, the prompt is identical, the observations are identical, the compute budget is identical, **only the memory state is deliberately changed**.

### Q.2 Paired conditions

```
Condition A:
  Memory says: "Object = red"
  Query: "What color is the object?"
  Expected answer: "red"

Condition B (counterfactual):
  Memory says: "Object = blue"  (counterfactually changed)
  Query: "What color is the object?"
  Expected answer: "blue"
```

### Q.3 What changes

- The memory state (one item's content is changed)

### Q.4 What remains fixed

- The underlying task and query
- The model and inference budget
- The observations (visual evidence)
- The prompt structure
- The compute budget

### Q.5 Causal estimand

```
τ_counterfactual = E[Y | memory_state_A] − E[Y | memory_state_B]
```

### Q.6 Expected causal direction

If memory has a causal effect, changing memory state from A to B should change the answer in the direction predicted by the memory change.

### Q.7 Counterfactual consistency rate (CCR)

```
CCR = P(answer changes in predicted direction | memory state changed)
```

Pre-registered threshold: CCR ≥ 0.70 is consistent with a causal memory effect.

### Q.8 Interpretation

- CCR ≈ 1.0: Memory has a strong causal effect on behavior
- CCR ≈ 0.5: Memory has no causal effect (answers are random with respect to memory)
- CCR ≈ 0.0: Memory has a paradoxical effect (opposite of predicted)

### Q.9 Types of counterfactual interventions

| Type | Description | Example |
|------|-------------|---------|
| Value substitution | Change a stored value | "red" → "blue" |
| Temporal reversal | Swap timestamps | Make old info appear new |
| Confidence manipulation | Change confidence metadata | 0.9 → 0.1 |
| Source substitution | Change source metadata | "admin" → "untrusted" |
| Addition | Add a false memory | Insert contradictory item |
| Removal | Remove a critical memory | Delete the only relevant item |

---

## R. Primary Metric

### R.1 Definition

**Primary Metric = Task Success Rate (TSR)**

```
TSR(S, r) = (1/N) · Σ success(t; S, r)
```

Where:
- `S` = system
- `r` = seed
- `N` = number of tasks in the frozen set
- `success(t; S, r) ∈ {0, 1}` = frozen deterministic predicate applied to the final answer

### R.2 Aggregation

```
TSR(S) = (1/R) · Σ_r TSR(S, r)
```

### R.3 Unit of analysis

Each (task × system × seed) cell is one observation.

### R.4 Treatment of special cases

| Case | Treatment |
|------|-----------|
| Empty/missing answer | Scored as failure (0) |
| Invalid model response | Scored as failure (0), labeled OTHER |
| Multiple questions | Each question scored separately; task success = all correct |
| Partial answers | No partial credit (binary) |
| Abstentions | Scored as failure (0) |

### R.5 Justification

TSR is appropriate because:
- The benchmark evaluates task completion, not partial knowledge
- The success criterion is deterministic and frozen
- It supports baseline-floor amounts for structurally trivial categories
- It is interpretable and comparable across systems

---

## S. Secondary Metrics

### S.1 Category success rate

TSR restricted to each category (retention, updating, stale_conflict, forgetting, adversarial, counterfactual).

### S.2 Management-critical score (MCS)

```
MCS = mean TSR over {updating, stale_conflict, forgetting, adversarial, counterfactual}
```

### S.3 Counterfactual consistency rate (CCR)

```
CCR = P(answer changes in predicted direction | memory state changed)
```

### S.4 Failure-category rate

Count of primary failure labels per category/system/seed.

### S.5 Retrieval quality metrics

| Metric | Definition |
|--------|-----------|
| Recall@k | Fraction of required items in top-k retrieved |
| Precision@k | Fraction of retrieved items that are relevant |
| Stale-memory retrieval rate | Fraction of queries where stale items are retrieved |
| Irrelevant-memory retrieval rate | Fraction of queries where irrelevant items are retrieved |

### S.6 Token overhead

Rendered memory-section tokens vs total prompt tokens.

### S.7 Store growth

Max store size reached per task.

### S.8 Latency

End-to-end latency, retrieval latency, memory operation latency, model latency.

---

## T. Calibration Protocol

### T.1 Confidence elicitation

If confidence is evaluated, the model is prompted to produce:

```
Answer: <answer>
Confidence: <value in [0, 1]>
```

### T.2 Confidence scale

- 0.0 = certain the answer is wrong
- 0.5 = uncertain
- 1.0 = certain the answer is correct

### T.3 Calibration metrics

| Metric | Definition |
|--------|-----------|
| Brier score | Mean squared error of confidence vs correctness |
| Expected Calibration Error (ECE) | Weighted average of |accuracy − confidence| across bins |

### T.4 Treatment of abstention

Abstentions are scored as failure (0) for TSR but reported separately.

### T.5 Applicability

Calibration metrics are only computed for systems that can produce comparable confidence outputs. If one system cannot produce confidence, calibration is reported only for those that can, with the limitation documented.

---

## U. Retrieval-Quality Metrics

### U.1 Recall@k

```
Recall@k = |{required items} ∩ {retrieved items}| / |{required items}|
```

### U.2 Precision@k

```
Precision@k = |{relevant items} ∩ {retrieved items}| / |{retrieved items}|
```

### U.3 Stale-memory retrieval rate

```
StaleRate = P(stale item ∈ retrieved set | stale item ∈ store)
```

### U.4 Irrelevant-memory retrieval rate

```
IrrelevantRate = P(irrelevant item ∈ retrieved set | irrelevant item ∈ store)
```

### U.5 Distinction from accuracy

Retrieval quality is **distinct** from final task accuracy. A system can retrieve the right items but still fail (reasoning failure), or retrieve wrong items but still succeed (lucky guess).

---

## V. Latency/Cost Measurement

### V.1 Latency

| Metric | Measurement |
|--------|------------|
| End-to-end latency | Task start to final answer |
| Retrieval latency | Query to retrieved items |
| Memory operation latency | Write/update/forget operation time |
| Model latency | Prompt to response |

### V.2 Cost

| Metric | Measurement |
|--------|------------|
| API calls | Number of model API calls |
| Tokens | Input/output token counts |
| Compute time | Wall-clock time |
| Storage | Memory store size |

### V.3 Zero-cost experiments

For experiments with no paid API usage, resource usage is reported rather than monetary costs.

---

## W. Failure Taxonomy

### W.1 Taxonomy

| Label | Definition | Detection |
|-------|-----------|-----------|
| `PERCEPTION_FAILURE` | Visual processing was confused by distractors | Manual + heuristic |
| `MEMORY_WRITE_FAILURE` | Item was not stored correctly | Store log check |
| `RETRIEVAL_FAILURE` | Required item absent from store at query | Store log check |
| `STALE_MEMORY_FAILURE` | Old/obsolete value in answer | Answer content check |
| `CONFLICT_RESOLUTION_FAILURE` | Both values appear without resolution | Answer content check |
| `DELETION_FAILURE` | Forgotten item retrieved or value in answer | Store/retrieval log |
| `COUNTERFACTUAL_MEMORY_FAILURE` | Answer did not change as predicted | Paired comparison |
| `DISTRACTOR_INTERFERENCE` | Distractor affected the answer | Answer content check |
| `IRRELEVANT_MEMORY_INTERFERENCE` | Required item outside top-k | Retrieval rank log |
| `REASONING_FAILURE` | Required items retrieved but answer wrong | Residual |
| `HALLUCINATION` | Answer contains information not in memory or context | Answer content check |
| `CALIBRATION_FAILURE` | Confidence miscalibrated | Calibration analysis |
| `BUDGET_FAILURE` | Token/context budget exceeded | Budget log |
| `SYSTEM_API_FAILURE` | Infrastructure error | Exception log |

### W.2 Classification procedure

Each failed task cell receives exactly **one primary label**, assigned by frozen priority order:

1. `SYSTEM_API_FAILURE` — infrastructure error
2. `BUDGET_FAILURE` — budget exceeded
3. `MEMORY_WRITE_FAILURE` — item not stored
4. `RETRIEVAL_FAILURE` — required item absent from store
5. `IRRELEVANT_MEMORY_INTERFERENCE` — required item outside top-k
6. `PERCEPTION_FAILURE` — visual confusion
7. `DISTRACTOR_INTERFERENCE` — distractor affected answer
8. `STALE_MEMORY_FAILURE` — old value in answer
9. `CONFLICT_RESOLUTION_FAILURE` — unresolved conflict
10. `DELETION_FAILURE` — forgotten item resurfaced
11. `COUNTERFACTUAL_MEMORY_FAILURE` — counterfactual not followed
12. `HALLUCINATION` — fabricated information
13. `REASONING_FAILURE` — residual wrong answer

### W.3 Multiplicity rules

- One primary label per cell
- Secondary annotations allowed for diagnosis
- Labels apply per (task × system × seed) cell

---

## X. Exact Success/Failure Criterion

### X.1 Deterministic predicate

```
success = contains_all(answer, required_values) AND NOT contains_any(answer, forbidden_values)
```

### X.2 Normalization

- `lower_strip`: lowercase, strip whitespace, collapse runs of whitespace
- `none`: no normalization

### X.3 Invalid response handling

| Response | Treatment |
|----------|-----------|
| Empty string | Failure (0) |
| None | Failure (0), labeled OTHER |
| Malformed | Failure (0), labeled OTHER |
| Timeout | Failure (0), labeled SYSTEM_API_FAILURE |

### X.4 No LLM judge

The primary metric uses **deterministic evaluation only**. No LLM judge is used for the primary metric. LLM judges may be used for secondary analysis with:
- Frozen judge prompt
- Reliability checks
- Bias analysis
- Blinding to system identity

---

## Y. Seeds

### Y.1 Pre-registered seeds

| Phase | Seeds |
|-------|-------|
| DEV | {42, 7, 2024} |
| HELD-OUT | {42, 7, 2024, 1337, 2718} |

### Y.2 Seed usage

- Task generation seeds: determine task content
- Run seeds: determine any stochasticity in the harness
- Bootstrap seeds: fixed at 12345 for analysis

### Y.3 Seed policy

- No seeds added after results exist
- No seeds removed after results exist
- All seeds reported, including unfavorable ones

---

## Z. Compute/API Budget

### Z.1 Budget

| Resource | Maximum |
|----------|---------|
| GPU hours | 0 (CPU-only) |
| CPU time | 8 hours per experiment |
| API calls | 10,000 per experiment |
| Tokens | 1M per experiment |
| Storage | 1 GB per experiment |
| Experiment duration | 24 hours |

### Z.2 Zero-cost development

Development experiments use:
- Deterministic mock models (no API)
- Local computation only
- No paid services

### Z.3 Live model experiments

Live model experiments require:
- Explicit written approval
- Documented API key (never committed)
- Budget monitoring
- Rate limiting

---

## AA. Stopping Rule

### AA.1 Pre-registered stopping criteria

An experiment is considered complete when:
1. All pre-registered seeds have been run
2. All frozen tasks have been evaluated
3. All systems have been run on all tasks
4. No infrastructure failures remain unresolved

### AA.2 Handling of system failures

| Failure | Handling |
|---------|----------|
| Single task failure | Labeled OTHER; run continues |
| System crash | Run restarted from beginning; failed run preserved |
| API rate limit | Exponential backoff; max 3 retries |
| Budget exceeded | Experiment stopped; partial results preserved |

### AA.3 No selective stopping

- No stopping based on results
- No adding runs after seeing undesirable results
- No removing unfavorable seeds
- The stopping rule is evaluated **before** results are inspected

---

## AB. Experiment Matrix

### AB.1 Systems

| ID | System | Description |
|----|--------|-------------|
| A | no_memory | No persistent memory |
| B | retrieval_only | Naive retrieval (append + top-k) |
| C | structured | Structured memory (typed records) |
| D | proposed | Proposed memory (active management) |
| E | full_context | Control (retrieval with top_k = all) |

### AB.2 Categories

| Category | Code | Intervention type |
|----------|------|-------------------|
| Retention | RET | None (baseline) |
| Updating | UPD | Authoritative update |
| Stale conflict | STL | Conflicting adds |
| Forgetting | FGT | Deletion directive |
| Adversarial | ADS | Untrusted injection |
| Counterfactual | CF | Memory state manipulation |
| Distractor | DIST | Irrelevant information |

### AB.3 Full matrix

Every system runs every task in every category. The full matrix is:

```
5 systems × 80 tasks × 5 seeds = 2,000 task evaluations
```

### AB.4 Counterfactual pairs

For the counterfactual category, each task has paired conditions:

```
5 systems × 16 CF tasks × 2 conditions × 5 seeds = 800 paired evaluations
```

---

## AC. Reproducibility Plan

### AC.1 Recorded metadata

Every experiment records:
- Git commit SHA (automatic)
- Experiment ID
- Benchmark version + hash
- Config hash
- Model identifier + version
- Prompt version
- Seeds
- Software environment (pip freeze)
- Timestamp
- Compute environment
- API provider (if applicable)
- Memory implementation version

### AC.2 Raw trajectory preservation

For every evaluated trajectory:
- Task ID, system, seed
- Observations (image references + text)
- Memory writes (item IDs + content)
- Memory state at query
- Retrieved memories (IDs + scores + ranks)
- Interventions applied
- Model inputs (exact prompts)
- Model outputs (verbatim)
- Confidence (if available)
- Latency
- Token/resource usage
- Final answer
- Ground truth
- Success/failure
- Failure category

### AC.3 Append-only results

- Results are never overwritten
- Run ID collisions raise errors
- Failed runs are preserved
- All seeds are reported

---

## AD. Protected-Run Policy

### AD.1 Development mode

**Allowed:**
- Debugging
- Small task subsets
- Mock models
- Local models
- Synthetic data
- Protocol refinement

**Not allowed:**
- Claiming research results
- Using held-out results to tune the protocol

### AD.2 Protected mode

**Requires:**
- Explicit protocol approval (this document, signed)
- Frozen held-out benchmark
- Frozen metrics
- Frozen interventions
- Frozen baselines
- Frozen seeds/stopping rules

**Authorization mechanism:**
- Protected config requires explicit `authorization_approved: true`
- Protected config references the approved protocol version
- Protected runs are logged with the authorization reference

### AD.3 Held-out protection

The held-out set must not be used for:
- Prompt tuning
- Memory design
- Intervention design
- Metric selection
- Threshold tuning
- Baseline tuning

After protocol freeze, the held-out set is protected.

---

## AE. Protocol Freeze Checklist

### AE.1 Freeze requirements

The protocol is frozen when all of the following are complete:

- [ ] Research question is explicit (§A)
- [ ] Hypotheses are explicit (§B)
- [ ] Predictions are explicit (§C)
- [ ] Alternative explanations are explicit (§D)
- [ ] Causal estimands are defined (§E)
- [ ] Data source is public or synthetic (§F)
- [ ] Dataset license/provenance is documented (§F)
- [ ] Train/dev/held-out split is frozen (§H)
- [ ] Memory eligibility rules are frozen (§I)
- [ ] No-memory baseline is defined (§J)
- [ ] Retrieval-only baseline is defined (§K)
- [ ] Proposed memory is defined (§L)
- [ ] Budgets are matched and documented (§M)
- [ ] Distractor intervention is frozen (§N)
- [ ] Stale/conflicting-memory intervention is frozen (§O)
- [ ] Deletion intervention is frozen (§P)
- [ ] Counterfactual intervention is frozen (§Q)
- [ ] Primary metric is frozen (§R)
- [ ] Secondary metrics are frozen (§S)
- [ ] Calibration protocol is frozen (§T)
- [ ] Retrieval-quality metrics are frozen (§U)
- [ ] Latency/cost methodology is frozen (§V)
- [ ] Failure taxonomy is frozen (§W)
- [ ] Success/failure criterion is frozen (§X)
- [ ] Seeds are specified (§Y)
- [ ] Compute/API budget is specified (§Z)
- [ ] Stopping rule is specified (§AA)
- [ ] Protocol version is frozen (this document)
- [ ] Protected comparison requires explicit authorization (§AD)
- [ ] Git SHA is recorded for experiments (§AC)
- [ ] Raw trajectories are preserved (§AC)
- [ ] Experiment log is maintained
- [ ] Negative results are preserved
- [ ] Inconclusive results are preserved
- [ ] Reused code/data/papers are cited
- [ ] Contributions are distinguished from reused components
- [ ] No private data is used
- [ ] No unauthorized paid compute/API is used
- [ ] The benchmark has not been weakened merely because of compute limitations

### AE.2 Freeze record

Upon approval, a freeze record is created with:
- Protocol version
- Approving signature
- Date
- Git commit SHA
- Benchmark hash
- Config hash
- Any approved deviations

### AE.3 Post-freeze changes

After freeze, any change to the protocol requires:
1. A new protocol version (v0.2, etc.)
2. A new benchmark version
3. A new approval
4. Preservation of the old version

---

## AF. Experiment Log

### AF.1 Format

```json
{
  "experiment_id": "...",
  "date": "...",
  "hypothesis": "...",
  "protocol_version": "v0.1",
  "change": "...",
  "reason": "...",
  "expected_effect": "...",
  "actual_result": "...",
  "failure": "...",
  "decision": "...",
  "next_action": "..."
}
```

### AF.2 Rules

- Include negative and inconclusive experiments
- Do not rewrite history
- Record all important experimental decisions

---

## AG. Data/Code Citations

### AG.1 Reused components

| Component | Source | License | What was reused |
|-----------|--------|---------|-----------------|
| Memory interface | SACAM v0.1 | MIT | Common interface design |
| Term-overlap retrieval | SACAM v0.1 | MIT | Deterministic retrieval |
| Failure taxonomy | SACAM v0.1 | MIT | Classification framework |
| Evaluator | SACAM v0.1 | MIT | Success predicate |
| Config system | SACAM v0.1 | MIT | Configuration management |

### AG.2 New components

| Component | Description |
|-----------|-------------|
| Counterfactual intervention layer | Paired memory state manipulation |
| Causal estimands | Formal causal inference framework |
| Multimodal observation interface | Image + text observations |
| Synthetic multimodal generator | Procedural scene generation |
| Counterfactual consistency rate | Causal effect measurement |
| Distractor intervention | Controlled irrelevant information |

### AG.3 Prior work

The SACAM v0.1 benchmark (this repository) provides the foundation. The causal memory evaluation extends it with:
- Formal causal intervention design
- Counterfactual paired conditions
- Multimodal observations
- Causal estimands and consistency metrics

---

## AH. Strongest Limitation

> **The strongest limitation of this causal evaluation is the synthetic nature of the benchmark.**

The benchmark uses procedurally generated synthetic multimodal tasks with invented entities. This design maximizes experimental control (ground truth, interventions, reproducibility) but sacrifices ecological validity. The causal effects measured here are effects **on this benchmark**, and generalization to real-world multimodal reasoning tasks is a separate empirical question that this benchmark cannot answer.

This limitation is acknowledged here, before any results, and is not a hidden weakness.

---

## AI. Final Acceptance Criteria

The project is complete only if:

- [ ] All protocol freeze checklist items (§AE) are complete
- [ ] The protected comparison has been run with explicit authorization
- [ ] Raw trajectories are preserved
- [ ] Git SHA is recorded
- [ ] Primary results table is populated from actual runs
- [ ] Secondary results are computed
- [ ] Calibration analysis is complete
- [ ] Retrieval quality analysis is complete
- [ ] Latency/cost analysis is complete
- [ ] Intervention effects are computed
- [ ] Failure analysis is complete
- [ ] Per-seed results are reported
- [ ] Confidence intervals/effect sizes are computed
- [ ] Negative/inconclusive findings are reported
- [ ] Strongest limitation is identified
- [ ] Final research audit is complete

---

*End of Protocol v0.1*
