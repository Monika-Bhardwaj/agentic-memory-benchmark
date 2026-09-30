# Implementation Plan — Causal Memory Evaluation

**Status:** DRAFT — pending protocol approval  
**Date:** 2026-09-30  
**Depends on:** `PROTOCOL_v0.1.md` approval

---

## Overview

This plan maps the frozen protocol to concrete implementation steps. **No implementation begins until the protocol is explicitly approved.**

The implementation is organized into milestones, each with clear deliverables, tests, and exit criteria.

---

## Milestone 0: Repository Preparation

### Goal
Prepare the repository for the new causal memory evaluation while preserving the existing SACAM v0.1 benchmark.

### Tasks

1. **Create protocol directory structure**
   - `protocol/PROTOCOL_v0.1.md` (done)
   - `protocol/IMPLEMENTATION_PLAN.md` (this file)
   - `protocol/freeze_record.md` (created at approval)

2. **Preserve existing benchmark**
   - Keep `benchmark/v0/` frozen and loadable
   - Keep `src/memory/` systems intact
   - Keep `experiments/run.py` and `experiments/analyze.py` functional
   - Add deprecation notice pointing to new protocol

3. **Create new directory structure**
   ```
   benchmark/v1/
   ├── SPEC.md
   ├── schema.json
   ├── task_manifest.json
   ├── tasks.jsonl (generated)
   └── fixtures/
   src/multimodal/
   ├── __init__.py
   ├── observation.py
   ├── scene_generator.py
   └── image_renderer.py
   src/interventions/
   ├── __init__.py
   ├── base.py
   ├── distractor.py
   ├── stale.py
   ├── deletion.py
   └── counterfactual.py
   src/causal/
   ├── __init__.py
   ├── estimands.py
   └── consistency.py
   configs/
   ├── causal_dev.yaml
   └── causal_protected.yaml
   ```

### Exit criteria
- [ ] Existing tests still pass
- [ ] New directory structure exists
- [ ] Protocol document is committed

---

## Milestone 1: Multimodal Observation Interface

### Goal
Implement the multimodal observation interface that supports images, text, and metadata.

### Tasks

1. **Implement `Observation` dataclass** (`src/multimodal/observation.py`)
   - Fields: `image`, `text`, `timestamp`, `metadata`
   - Validation: no ground truth in metadata
   - Serialization: to/from dict

2. **Implement scene generator** (`src/multimodal/scene_generator.py`)
   - Procedural generation of visual scenes
   - Deterministic given seed
   - Supports: objects, colors, positions, spatial relationships
   - Supports: temporal dynamics (movement, appearance, disappearance)
   - Supports: distractor objects

3. **Implement image renderer** (`src/multimodal/image_renderer.py`)
   - Render scenes to PNG images
   - Deterministic given scene specification
   - Store images with content-addressable references

4. **Implement multimodal task loader** (`src/tasks/multimodal_loader.py`)
   - Load tasks with image references
   - Validate image existence
   - Compute benchmark hash

### Tests
- [ ] Observation serialization roundtrip
- [ ] Scene generator determinism (same seed → same scene)
- [ ] Image renderer produces valid PNG
- [ ] No ground truth leakage in metadata
- [ ] Multimodal task loader validates correctly

### Exit criteria
- [ ] All tests pass
- [ ] Can generate a multimodal task end-to-end
- [ ] Images are deterministic and reproducible

---

## Milestone 2: Intervention Framework

### Goal
Implement the formal intervention abstraction with deterministic, versioned interventions.

### Tasks

1. **Implement `Intervention` base class** (`src/interventions/base.py`)
   ```python
   class Intervention(abc.ABC):
       def apply(self, trajectory, memory_state): ...
       def describe(self): ...
       def expected_effect(self): ...
   ```

2. **Implement distractor intervention** (`src/interventions/distractor.py`)
   - Add irrelevant visual objects
   - Add irrelevant textual facts
   - Control: what changes, what remains fixed

3. **Implement stale/conflicting intervention** (`src/interventions/stale.py`)
   - Create conflicting memory entries
   - Control: initial observation, new observation, query

4. **Implement deletion intervention** (`src/interventions/deletion.py`)
   - Remove items from memory
   - Control: before/after deletion behavior

5. **Implement counterfactual intervention** (`src/interventions/counterfactual.py`)
   - Paired conditions with only memory state changed
   - Control: intervention variable, treatment, control
   - Measure: counterfactual consistency rate

### Tests
- [ ] Intervention determinism
- [ ] Distractor intervention adds irrelevant info
- [ ] Stale intervention creates conflict
- [ ] Deletion intervention removes items
- [ ] Counterfactual intervention changes only memory state
- [ ] Interventions do not inspect outcomes

### Exit criteria
- [ ] All tests pass
- [ ] Each intervention is independently testable
- [ ] Interventions are composable

---

## Milestone 3: Causal Estimands and Consistency

### Goal
Implement the causal estimation framework.

### Tasks

1. **Implement estimands** (`src/causal/estimands.py`)
   - `average_memory_effect()`
   - `retrieval_effect()`
   - `memory_management_effect()`
   - `intervention_effect()`
   - `category_specific_effect()`

2. **Implement counterfactual consistency** (`src/causal/consistency.py`)
   - `counterfactual_consistency_rate()`
   - Paired comparison logic
   - Direction prediction

3. **Implement causal analysis** (`src/analysis/causal.py`)
   - Compute all estimands from raw results
   - Bootstrap confidence intervals
   - Effect sizes (Cohen's h, risk difference)

### Tests
- [ ] Estimands compute correctly on synthetic data
- [ ] CCR = 1.0 when memory has perfect causal effect
- [ ] CCR ≈ 0.5 when memory has no causal effect
- [ ] Bootstrap CIs are reasonable

### Exit criteria
- [ ] All tests pass
- [ ] Can compute all estimands from raw results
- [ ] CCR is correctly computed

---

## Milestone 4: Benchmark v1 Task Generation

### Goal
Generate the frozen benchmark v1 task set.

### Tasks

1. **Design task schema** (`benchmark/v1/schema.json`)
   - Extend v0 schema with multimodal fields
   - Add counterfactual pair fields
   - Add intervention metadata

2. **Design task manifest** (`benchmark/v1/task_manifest.json`)
   - 80 tasks across 7 categories
   - Balanced difficulty
   - DEV/HELD-OUT split by seed

3. **Implement generator** (`src/tasks/v1_generator.py`)
   - Procedural multimodal scene generation
   - Event sequence construction
   - Intervention application
   - Validation

4. **Generate and freeze tasks**
   - Generate DEV tasks (seeds 1000–1999)
   - Generate HELD-OUT tasks (seeds 5000–5999)
   - Compute and record benchmark hash
   - Commit to repository

### Tests
- [ ] All generated tasks validate against schema
- [ ] DEV and HELD-OUT splits are disjoint
- [ ] Task generation is deterministic
- [ ] Benchmark hash is stable
- [ ] No ground truth leakage

### Exit criteria
- [ ] 80 tasks generated and committed
- [ ] Benchmark hash recorded
- [ ] All validation passes
- [ ] Tasks are human-inspectable

---

## Milestone 5: Systems Implementation

### Goal
Implement all memory systems for the causal evaluation.

### Tasks

1. **No-memory baseline** (already exists, adapt for multimodal)
2. **Retrieval-only baseline** (already exists, adapt for multimodal)
3. **Structured memory baseline** (already exists, adapt for multimodal)
4. **Proposed memory system** (extend SACAM v1 with multimodal support)
5. **Full-context control** (already exists, adapt for multimodal)

### Tests
- [ ] All systems implement the common interface
- [ ] All systems handle multimodal observations
- [ ] All systems are deterministic given seed
- [ ] Systems are interchangeable in the harness

### Exit criteria
- [ ] All tests pass
- [ ] All systems run on all task categories
- [ ] Systems are behind the common interface

---

## Milestone 6: Experiment Runner and Analysis

### Goal
Implement the experiment runner and analysis pipeline for the causal evaluation.

### Tasks

1. **Extend experiment runner** (`experiments/run.py`)
   - Support multimodal tasks
   - Support counterfactual pairs
   - Support intervention metadata
   - Record all causal-relevant data

2. **Extend analysis** (`experiments/analyze.py`)
   - Compute causal estimands
   - Compute CCR
   - Generate causal results table
   - Generate failure analysis

3. **Implement causal report generator**
   - Primary results table
   - Causal effects table
   - Counterfactual consistency table
   - Failure analysis
   - Negative/inconclusive findings

### Tests
- [ ] Runner produces all required raw data
- [ ] Analysis computes all metrics correctly
- [ ] Causal estimands are computed from raw data
- [ ] Report is generated automatically

### Exit criteria
- [ ] End-to-end run works with mock model
- [ ] All metrics computed correctly
- [ ] Report is generated

---

## Milestone 7: Development Experiments

### Goal
Run development experiments to validate the instrument.

### Tasks

1. **Smoke test** (mock model, small subset)
   - Validate all components work together
   - Check failure classification
   - Verify raw log sufficiency

2. **DEV run** (mock model, all DEV tasks)
   - Validate full pipeline
   - Check metric computation
   - Verify causal estimands

3. **Instrument validation**
   - Verify interventions work as designed
   - Verify counterfactual pairs produce expected patterns
   - Verify failure taxonomy covers observed failures

### Exit criteria
- [ ] Smoke test passes
- [ ] DEV run completes
- [ ] All metrics compute correctly
- [ ] No instrument defects remain
- [ ] Results labeled as instrument validation only

---

## Milestone 8: Protected Evaluation (REQUIRES EXPLICIT AUTHORIZATION)

### Goal
Run the frozen protected comparison on the held-out set.

### Prerequisites
- [ ] Protocol explicitly approved
- [ ] All development experiments complete
- [ ] All instrument defects resolved
- [ ] Authorization recorded in config

### Tasks

1. **Run protected experiment**
   - All systems × all HELD-OUT tasks × all seeds
   - Record all raw trajectories
   - Record Git SHA, config, metadata

2. **Generate protected analysis**
   - Primary results table
   - Causal effects table
   - Counterfactual consistency table
   - Failure analysis
   - Calibration analysis
   - Retrieval quality analysis
   - Latency/cost analysis

3. **Generate protected report**
   - All results from actual runs
   - Negative/inconclusive findings
   - Strongest limitation
   - Final research audit

### Exit criteria
- [ ] Protected run completes
- [ ] All raw trajectories preserved
- [ ] All metrics computed
- [ ] Report generated
- [ ] No manual edits to results

---

## Milestone 9: Research Audit and Documentation

### Goal
Act as a skeptical reviewer and document findings.

### Tasks

1. **Scientific validity review**
   - Did the intervention actually manipulate memory?
   - Was anything else changed simultaneously?
   - Are the causal claims identifiable?
   - Are the baselines fair?

2. **Benchmark validity review**
   - Are the tasks sufficiently realistic?
   - Are the interventions meaningful?
   - Is the benchmark too easy?
   - Is the held-out set genuinely protected?

3. **Statistical validity review**
   - Are seeds sufficient?
   - Are uncertainty estimates appropriate?
   - Are multiple comparisons handled?
   - Are conclusions stronger than the sample supports?

4. **Reproducibility review**
   - Can another researcher reproduce the result?
   - Are raw trajectories preserved?
   - Can every result be traced to a specific experiment?

5. **Final documentation**
   - Update README
   - Update AGENTS.md
   - Write research review
   - Document limitations

### Exit criteria
- [ ] All review questions answered
- [ ] Documentation complete
- [ ] Limitations documented
- [ ] Negative results preserved

---

## Dependency Graph

```
M0: Repository Preparation
    ↓
M1: Multimodal Observation Interface
    ↓
M2: Intervention Framework
    ↓
M3: Causal Estimands and Consistency
    ↓
M4: Benchmark v1 Task Generation
    ↓
M5: Systems Implementation
    ↓
M6: Experiment Runner and Analysis
    ↓
M7: Development Experiments
    ↓
M8: Protected Evaluation (REQUIRES AUTHORIZATION)
    ↓
M9: Research Audit and Documentation
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Protocol requires revision | Medium | High | Thorough review before approval |
| Task generation is non-deterministic | Low | High | Extensive testing in M1 |
| Interventions don't isolate memory | Medium | High | Careful design + validation in M7 |
| CCR is near 0.5 (no causal effect) | Medium | Medium | This is a valid result; report honestly |
| Model nondeterminism | Medium | Low | Multiple seeds; temperature 0 |
| Budget exceeded | Low | Medium | Pre-registered budget monitoring |
| Held-out contamination | Low | High | Strict DEV/HELD-OUT separation |

---

## Success Criteria

The implementation is successful if:

1. The protocol is frozen and approved
2. All development experiments validate the instrument
3. The protected comparison runs successfully
4. Raw trajectories are preserved
5. All metrics are computed correctly
6. The report is generated automatically
7. Negative and inconclusive results are preserved
8. The strongest limitation is identified
9. The research audit is complete

---

*End of Implementation Plan*
