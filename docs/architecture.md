# Architecture (Proposed)

Planned structure and interfaces for the implementation milestone. Approved with the
protocol; concrete code lands only in Milestone 2. The common memory interface and the
runner data flow are specified here because the protocol depends on them.

## 1. Intended layout

```
agentic-memory-benchmark/
├── README.md
├── LICENSE
├── pyproject.toml
├── APPROVAL_REQUEST.md
├── benchmark/
│   └── v0/
│       ├── SPEC.md
│       ├── schema.json
│       ├── task_manifest.json       (frozen allocation)
│       ├── tasks.jsonl              (generated, committed, hashed — the frozen set)
│       └── fixtures/                (5 example fixtures)
├── src/
│   ├── agents/                      (agent harness; mock model; live model adapter)
│   ├── memory/                      (common interface + 4 systems)
│   ├── tasks/                       (loader, validation, generation)
│   ├── evaluation/                  (evaluator: success predicate)
│   ├── metrics/                     (TSR, secondary metrics)
│   ├── analysis/                    (tables, figures from raw results only)
│   └── utils/                       (hashing, seeding, json logging, config)
├── baselines/                       (no_memory, naive_retrieval, structured_memory —
                                      each a thin entry inside src/memory, kept as
                                      explicit registry entries, not duplicated code)
├── sacam/                           (sacam_v0 plugin entry + placeholder for full work)
├── configs/                         (smoke.yaml, benchmark_v0.yaml, .env.example)
├── experiments/
│   └── run.py                       (unified runner; random seed; loads everything)
├── results/
│   ├── raw/<experiment_id>/<run_id>/   (append-only; never overwritten)
│   ├── processed/  tables/  figures/  logs/
├── tests/                           (schema, generation, memory ops, evaluator, metrics,
                                      config, reproducibility, end-to-end smoke with mock)
└── docs/                            (this document set)
```

Rationale: `baselines/` and `sacam/` are registries of the systems under test rather than
duplicated code — all implementations live behind the `src/memory` interface. This keeps
the comparison apples-to-apples and single-source.

## 2. Common memory interface (spec)

All four systems implement the same protocol against the directive stream. Semantics are
frozen:

```python
class Memory:
    def add(self, item: MemoryItem) -> None          # store item
    def update(self, item_id: str, item: MemoryItem) -> None  # authoritative replace
    def forget(self, item_id: str) -> None           # remove from store
    def retrieve(self, query: str, top_k: int) -> list[RetrievedItem]  # ranked read
    def inspect(self) -> list[MemoryItem]           # full store snapshot (logging)
```

- `MemoryItem` = `{item_id, content, metadata{source, timestamp, confidence, adversarial, authority}}`.
- `RetrievedItem` = memory item + retrieval score + rank (must expose **rank per id** for
  automatic failure attribution).
- **Determinism rule:** every random operation seeds from the run seed; no hidden RNG.
- **Equality rule:** the harness logs every op (op, args, result item ids), so the store
  and retrieval behavior is fully reproducible from logs alone.

## 3. Agent and model adapters

- `AgentHarness`: replays events, renders (pinned renderer), produces final answer for
  grading; identical for all systems.
- `MockModel`: deterministic scripted responses for tests and smoke-infrastructure runs —
  **no API needed** to validate the instrument.
- `LiveModelAdapter`: provider API (env-var key only), timeouts, rate-limit backoff,
  malformed-response handling, temperature from config; model/version recorded.

## 4. Runner data flow (`experiments/run.py`)

1. load configuration (configs/<experiment>.yaml)
2. initialize deterministic seed(s)
3. load frozen benchmark (tasks.jsonl for the pinned version)
4. initialize model (mock or live)
5. initialize agent harness
6. initialize the configured memory system
7. execute tasks (fixed order; memory reset per task)
8. record trajectory/output + memory-op log + retrieval rank log
9. evaluate success/failure (frozen predicate)
10. categorize failures (frozen priority procedure)
11. compute metrics (TSR + secondary, per-seed)
12. save raw results, configuration, and experiment metadata (append-only)

## 5. Configuration schema (frozen shape)

```yaml
experiment:
  name: smoke_v0
  benchmark_version: v0.1
  seed: 42            # also full seed lists live here
model:
  name: mock           # or provider/model
  temperature: 0
memory:
  enabled: true
  type: naive_retrieval
  retrieval_top_k: 3
  memory_budget_items: 512
evaluation:
  primary_metric: tsr
  mme: 0.05
  retention_tolerance: -0.05
```

The manifest of *every* file and value changes is captured by a config hash recorded in
metadata. Nothing is hard-coded in the runner.

## 6. Logging

- Structured JSONL logs per run: system, seed, task_id, event rendering, memory ops,
  retrieval ranks, final answer, predicate outcome, primary failure label.
- Human-readable transcript mirror per run for qualitative inspection.
- All results trees are append-only; `run_id` collisions raise an error rather than
  overwrite.

## 7. Analysis

One script family reads only `results/raw/...` and emits processed tables/figures
(never hand-edited). Analysis covers: primary table, per-category tables, failure rates,
seed-level distributions, bootstrap CIs, token overhead, store growth. Figure generation
is optional and off by default in CI to avoid binary bloat.