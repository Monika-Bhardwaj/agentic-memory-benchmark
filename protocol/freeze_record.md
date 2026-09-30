# Protocol Freeze Record

**Protocol Version:** v0.2  
**Date:** 2026-10-01  
**Status:** FROZEN — pending external review

## Freeze Summary

The causal memory evaluation protocol v0.2 is frozen. This document records the freeze event and serves as the reference for all protected experiments.

## Frozen Components

| Component | Version | Hash/Status |
|-----------|---------|-------------|
| Protocol specification | v0.2 | `protocol/PROTOCOL_v0.2.md` |
| Benchmark v1 | v1 | `3ab9f94052df61bfd56e1619c5013d7eda14d70366c449e9671610946e144639` |
| Task schema | v1 | `benchmark/v1/schema.json` |
| Task manifest | v1 | `benchmark/v1/task_manifest.json` |
| Config (DEV) | v1 | `configs/causal_dev.yaml` |
| Config (protected) | v1 | `configs/causal_protected.yaml` |
| Prompt version | v1-p1 | Frozen |
| Memory interface | v1 | Frozen |
| Evaluation protocol | v0.2 | Frozen |
| Intervention definitions | v0.2 | Frozen |

## Frozen Seeds

| Phase | Seeds |
|-------|-------|
| DEV | {42, 7, 2024} |
| HELD-OUT | {42, 7, 2024, 1337, 2718} |

## Frozen Systems

| ID | System |
|----|--------|
| A | no_memory |
| B | naive_retrieval |
| C | structured_memory |
| D | sacam_v1 (proposed) |
| E | full_context (control) |

## Frozen Categories

| Category | Code | Intervention |
|----------|------|-------------|
| Retention | RET | None |
| Updating | UPD | Authoritative update |
| Stale conflict | STL | Conflicting adds |
| Forgetting | FGT | Deletion directive |
| Adversarial | ADS | Untrusted injection |
| Counterfactual | CF | Memory state manipulation |
| Distractor | DIST | Irrelevant information |

## Frozen Metrics

- **Primary metric:** Task Success Rate (TSR)
- **Secondary metrics:** MCS, category success rates, CCR, failure rates, retrieval quality
- **MME:** +0.05
- **Retention tolerance:** -0.05

## Frozen Budgets

| Budget | Value |
|--------|-------|
| Context tokens | 4096 |
| Retrieval items | top_k = 3 |
| Memory budget | 512 items |
| Output tokens | 512 |
| Temperature | 0 |
| **Retries** | **0 (zero retries for primary metric)** |

## Frozen Task Split

| Split | Task count | Seed range |
|-------|-----------|-------------|
| DEV | 40 | 1000–1999 |
| HELD-OUT | 40 | 5000–5999 |
| **Total** | **80** | — |

## Approval

**Status:** Pending external review  
**Date:** 2026-10-01  
**Reviewer:** (external reviewer pending)

## Post-Freeze Policy

After this freeze:
1. No changes to the protocol without a new version (v0.3)
2. No changes to the benchmark tasks
3. No changes to the metrics or decision rules
4. No tuning on held-out data
5. All experiments reference this protocol version
6. Any discovered defects require a new protocol version

## Strongest Limitation

> The strongest limitation of this causal evaluation is the synthetic nature of the benchmark. The causal effects measured here are effects **on this benchmark**, and generalization to real-world multimodal reasoning is a separate empirical question.

---

*This document is part of the frozen protocol and is never edited after the first protected run.*
