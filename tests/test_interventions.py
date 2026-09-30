"""Tests for intervention framework."""

import pytest

from src.interventions.base import Intervention, InterventionResult
from src.interventions.counterfactual import CounterfactualIntervention
from src.interventions.deletion import DeletionIntervention
from src.interventions.distractor import DistractorIntervention
from src.interventions.stale import StaleConflictIntervention


class TestDistractorIntervention:
    def test_apply(self):
        intervention = DistractorIntervention(n_distractors=2, distractor_type="textual")
        trajectory = {"events": [{"event_id": "e1", "kind": "query", "text": "Test?"}]}
        memory_state = {}
        result = intervention.apply(trajectory, memory_state)
        assert result.success
        assert len(trajectory["events"]) == 3  # 2 distractors + 1 query
        assert "distractor_event_ids" in trajectory

    def test_describe(self):
        intervention = DistractorIntervention(n_distractors=3)
        desc = intervention.describe()
        assert "3" in desc
        assert "distractor" in desc.lower()

    def test_expected_effect(self):
        intervention = DistractorIntervention(n_distractors=1)
        effect = intervention.expected_effect()
        assert "should NOT be affected" in effect

    def test_validate(self):
        intervention = DistractorIntervention(n_distractors=-1)
        errors = intervention.validate()
        assert len(errors) > 0


class TestStaleConflictIntervention:
    def test_apply(self):
        intervention = StaleConflictIntervention(
            entity="Object A", old_value="X", new_value="Y"
        )
        trajectory = {"events": [{"event_id": "e1", "kind": "query", "text": "Where?"}]}
        memory_state = {}
        result = intervention.apply(trajectory, memory_state)
        assert result.success
        assert "conflict" in trajectory

    def test_validate_same_values(self):
        intervention = StaleConflictIntervention(old_value="same", new_value="same")
        errors = intervention.validate()
        assert any("differ" in e for e in errors)


class TestDeletionIntervention:
    def test_apply(self):
        intervention = DeletionIntervention(
            item_id="m1", item_content="Meeting: 3pm."
        )
        trajectory = {"events": [{"event_id": "e1", "kind": "query", "text": "When?"}]}
        memory_state = {}
        result = intervention.apply(trajectory, memory_state)
        assert result.success
        assert "deletion" in trajectory

    def test_validate(self):
        intervention = DeletionIntervention(item_id="", item_content="")
        errors = intervention.validate()
        assert len(errors) > 0


class TestCounterfactualIntervention:
    def test_apply_condition_a(self):
        intervention = CounterfactualIntervention(
            entity="Object", value_a="red", value_b="blue"
        )
        trajectory = {"events": [{"event_id": "e1", "kind": "query", "text": "Color?"}]}
        memory_state = {"condition": "A"}
        result = intervention.apply(trajectory, memory_state)
        assert result.success
        assert trajectory["counterfactual"]["condition"] == "A"
        assert trajectory["counterfactual"]["expected_answer"] == "red"

    def test_apply_condition_b(self):
        intervention = CounterfactualIntervention(
            entity="Object", value_a="red", value_b="blue"
        )
        trajectory = {"events": [{"event_id": "e1", "kind": "query", "text": "Color?"}]}
        memory_state = {"condition": "B"}
        result = intervention.apply(trajectory, memory_state)
        assert result.success
        assert trajectory["counterfactual"]["condition"] == "B"
        assert trajectory["counterfactual"]["expected_answer"] == "blue"

    def test_apply_pair(self):
        intervention = CounterfactualIntervention(
            entity="Object", value_a="red", value_b="blue"
        )
        trajectory = {"events": [{"event_id": "e1", "kind": "query", "text": "Color?"}]}
        traj_a, traj_b = intervention.apply_pair(trajectory)
        assert traj_a["counterfactual"]["condition"] == "A"
        assert traj_b["counterfactual"]["condition"] == "B"
        assert traj_a["counterfactual"]["expected_answer"] == "red"
        assert traj_b["counterfactual"]["expected_answer"] == "blue"

    def test_validate_same_values(self):
        intervention = CounterfactualIntervention(value_a="same", value_b="same")
        errors = intervention.validate()
        assert any("differ" in e for e in errors)

    def test_expected_effect(self):
        intervention = CounterfactualIntervention()
        effect = intervention.expected_effect()
        assert "causal" in effect.lower()
        assert "CCR" in effect
