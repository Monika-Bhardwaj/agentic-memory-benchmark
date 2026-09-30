"""Tests for causal estimands and consistency measurement."""

import pytest

from src.causal.estimands import (
    average_memory_effect,
    bootstrap_ci,
    category_specific_effect,
    cohens_h,
    intervention_effect,
    memory_management_effect,
    retrieval_effect,
)
from src.causal.consistency import counterfactual_consistency_rate, paired_comparison


class TestEstimands:
    def test_average_memory_effect(self):
        outcomes_memory = [{"success": 1}, {"success": 1}, {"success": 0}]
        outcomes_no_memory = [{"success": 0}, {"success": 1}, {"success": 0}]
        result = average_memory_effect(outcomes_memory, outcomes_no_memory)
        assert result["estimand"] == "average_memory_effect"
        assert result["value"] == pytest.approx(0.333, rel=0.1)

    def test_retrieval_effect(self):
        outcomes_retrieval = [{"success": 1}, {"success": 1}]
        outcomes_no_memory = [{"success": 0}, {"success": 0}]
        result = retrieval_effect(outcomes_retrieval, outcomes_no_memory)
        assert result["value"] == pytest.approx(1.0)

    def test_memory_management_effect(self):
        outcomes_proposed = [{"success": 1}, {"success": 1}]
        outcomes_retrieval = [{"success": 1}, {"success": 0}]
        result = memory_management_effect(outcomes_proposed, outcomes_retrieval)
        assert result["value"] == pytest.approx(0.5)

    def test_intervention_effect(self):
        outcomes_a = [{"success": 1}, {"success": 1}]
        outcomes_b = [{"success": 0}, {"success": 0}]
        result = intervention_effect(outcomes_a, outcomes_b)
        assert result["value"] == pytest.approx(1.0)

    def test_category_specific_effect(self):
        outcomes_proposed = [
            {"success": 1, "category": "retention"},
            {"success": 0, "category": "updating"},
        ]
        outcomes_retrieval = [
            {"success": 1, "category": "retention"},
            {"success": 1, "category": "updating"},
        ]
        result = category_specific_effect(outcomes_proposed, outcomes_retrieval, "updating")
        assert result["value"] == pytest.approx(-1.0)

    def test_empty_inputs(self):
        result = average_memory_effect([], [])
        assert result["value"] is None

    def test_bootstrap_ci(self):
        values = [0.5, 0.6, 0.7, 0.8, 0.9]
        lo, hi = bootstrap_ci(values, n_bootstrap=100, seed=42)
        assert lo <= hi
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0

    def test_cohens_h(self):
        h = cohens_h(0.5, 0.3)
        assert h > 0  # p1 > p2 should give positive h


class TestCounterfactualConsistency:
    def test_perfect_consistency(self):
        paired = [
            {
                "condition_a": {"answer": "red", "success": True},
                "condition_b": {"answer": "blue", "success": False},
                "expected_direction": "A",
            }
            for _ in range(10)
        ]
        result = counterfactual_consistency_rate(paired)
        assert result["ccr"] == pytest.approx(1.0)
        assert result["n_consistent"] == 10

    def test_no_consistency(self):
        paired = [
            {
                "condition_a": {"answer": "red", "success": False},
                "condition_b": {"answer": "blue", "success": True},
                "expected_direction": "A",
            }
            for _ in range(10)
        ]
        result = counterfactual_consistency_rate(paired)
        assert result["ccr"] == pytest.approx(0.0)

    def test_empty_pairs(self):
        result = counterfactual_consistency_rate([])
        assert result["ccr"] is None

    def test_paired_comparison_consistent(self):
        outcome_a = {"answer": "red", "success": True}
        outcome_b = {"answer": "blue", "success": False}
        result = paired_comparison(outcome_a, outcome_b, expected_direction="A")
        assert result["consistent"]
        assert result["answer_changed"]

    def test_paired_comparison_inconsistent(self):
        outcome_a = {"answer": "red", "success": False}
        outcome_b = {"answer": "blue", "success": True}
        result = paired_comparison(outcome_a, outcome_b, expected_direction="A")
        assert not result["consistent"]
