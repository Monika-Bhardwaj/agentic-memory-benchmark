# Reproducibility Specification (Frozen v0.1)

Controls that let another researcher recreate any run byte-for-byte where the model
allows, and diagnose the only irreducible nondeterminism (the LLM) precisely.

## 1. Minimal reproducibility contract

To reproduce a reported number, a researcher needs:

1. **The frozen benchmark** — `benchmark/v0/tasks.jsonl` + `benchmark_hash` (SHA-256)
   recorded in the pre-registration manifest. Version pinned by config `benchmark_version`.
2. **The frozen config** — a committed YAML plus its config hash, recorded per run.
3. **Seeds** — the pre-registered list and the per-run seed.
4. **The model** — provider, exact model id, version if available, temperature, sampling
   params. In practice, many providers change under the hood; therefore the *claim* is
   "reproducible conditional on the documented model artifact", not "the same digits
   forever".
5. **Software env** — `requirements.txt`/`pyproject` pinned, Python version, `pip freeze`
   snapshot saved per experiment.
6. **Code** — git commit recorded in every run's metadata.
7. **Raw outputs** — append-only `results/raw/<experiment_id>/<run_id>/`.

## 2. Seed policy

- Smoke: `{42, 7, 2024}`; full: `{42, 7, 2024, 1337, 2718}`.
- Seed is used for: task-local variance (if any), deterministic retrieval internals, and
  any RNG in the harness/analysis. Each is named in logs (`seed_source`).
- The bootstrap in analysis uses its own fixed seed (declared), decoupled from run seeds.
- Never select, drop, or add seeds after seeing results.

## 3. Raw results layout (append-only)

```
results/raw/<experiment_id>/
├── run_<system>_<seed>/
│   ├── metadata.json        (run_id, git commit, timestamps, config hash, model info)
│   ├── config.yaml          (exact copy used)
│   ├── transcript.jsonl      (rendered events + memory-section texts + model outputs)
│   ├── memory_ops.jsonl      (every directive + outcome)
│   ├── retrieval.jsonl       (query, ranks, scores, item ids returned)
│   ├── tasks.jsonl           (copy of the frozen task subset or full file reference + hash)
│   └── outcomes.jsonl        (per-task: answer, predicate result, primary label, secondary)
├── aggregate.log
└── run_manifest.json
```

Rules: no overwrites; `run_id` uniqueness enforced; failures crash with a written error
record rather than a partially-written success.

## 4. Environment and secrets

- API keys only via env vars (`LLM_API_KEY`, provider equivalents); `.env.example`
  committed, `.env` git-ignored.
- `requirements.txt` + `pyproject.toml` pin dependencies at Milestone 2.
- Timeouts, rate-limit backoff, and malformed-response handling are implemented and
  logged; a failed call is a failed cell (label `OTHER`), never a silent retry that would
  hide nondeterminism — retry policy, if any, is declared in config.

## 5. Versioning rules

- Benchmark: `v0.1` frozen forever; changes → `v0.2` (tasks, categories, schema,
  generation, decision rules). Old versions remain committed.
- Protocol: mirrored in the pre-registration manifest (`protocol_version`).
- The manifest (created at approval) records: benchmark hash, config schema hash, seeds,
  MME, E-rule text, renderer/prompt versions, approving party, date, commit SHA.

## 6. What is not reproducible by design (and why we say so)

- **LLM sampling at temperature 0** may still vary across provider versions; we record
  the model artifact and spread across seeds, and we state the conditional claim.
- **Human inspection of failures** (a random subset per category) is a *documented
  qualitative step*, stored as notes, and never enters the primary metric.
- **Future provider changes** after an experiment are a reproducibility hazard; the
  frozen model artifact and env snapshot bound the problem.