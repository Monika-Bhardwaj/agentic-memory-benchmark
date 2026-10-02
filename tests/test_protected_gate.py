"""Tests for protected run fail-closed gate.

Verifies that the Python runner rejects protected runs when authorization
is false or missing, BEFORE loading tasks or constructing the model.
"""

import pytest
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_config


class TestProtectedGate:
    """Test that protected runs are blocked without authorization."""

    def test_protected_config_has_approval_false(self):
        """Protected config must have authorization_approved: false."""
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        assert cfg.authorization_approved is False

    def test_protected_config_references_v02(self):
        """Protected config must reference protocol v0.2."""
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        assert cfg.protocol_version == "v0.2"

    def test_protected_config_has_frozen_model(self):
        """Protected config must have a frozen model name."""
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        assert cfg.model["name"] != "REPLACE_WITH_MODEL"
        assert cfg.model["name"] != ""

    def test_dev_config_has_no_approval_requirement(self):
        """DEV config does not require authorization."""
        cfg = load_config(ROOT / "configs" / "causal_dev.yaml")
        assert cfg.phase == "dev"
        assert cfg.authorization_approved is False

    def test_config_hash_includes_authorization(self):
        """Config hash must include authorization_approved field."""
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        hash1 = cfg.hash()
        cfg.authorization_approved = True
        hash2 = cfg.hash()
        assert hash1 != hash2

    def test_config_hash_includes_protocol_version(self):
        """Config hash must include protocol_version field."""
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        hash1 = cfg.hash()
        cfg.protocol_version = "v0.1"
        hash2 = cfg.hash()
        assert hash1 != hash2

    def test_runner_blocks_unapproved_protected_run(self):
        """Direct Python invocation of protected run must be rejected."""
        from experiments.run_causal import run_causal
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        assert cfg.authorization_approved is False
        with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED"):
            run_causal(ROOT / "configs" / "causal_protected.yaml")

    def test_runner_blocks_wrong_protocol_version(self):
        """Protected run with wrong protocol version must be rejected."""
        from experiments.run_causal import run_causal

        # Create a temporary config with authorization=True but wrong protocol
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_protected",
                    "benchmark_version": "v1",
                    "phase": "protected",
                    "seeds": [42],
                    "authorization_approved": True,
                    "protocol_version": "v0.1",  # Wrong version
                },
                "model": {"name": "gpt-4.1-mini", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            # Patch task loading and model construction to fail if reached
            with patch('experiments.run_causal.load_v1_tasks') as mock_load, \
                 patch('experiments.run_causal.build_model') as mock_model:
                mock_load.side_effect = AssertionError("Task loading should not be reached!")
                mock_model.side_effect = AssertionError("Model construction should not be reached!")

                with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED.*protocol_version"):
                    run_causal(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_runner_blocks_unknown_phase(self):
        """Unknown phase must be rejected before task loading."""
        from experiments.run_causal import run_causal

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_unknown",
                    "benchmark_version": "v1",
                    "phase": "unknown_phase",
                    "seeds": [42],
                },
                "model": {"name": "gpt-4.1-mini", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with patch('experiments.run_causal.load_v1_tasks') as mock_load:
                mock_load.side_effect = AssertionError("Task loading should not be reached!")
                with pytest.raises(RuntimeError, match="UNKNOWN PHASE"):
                    run_causal(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_runner_blocks_missing_protocol_version(self):
        """Protected config without explicit protocol_version must be rejected."""
        from experiments.run_causal import run_causal

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_missing_protocol",
                    "benchmark_version": "v1",
                    "phase": "protected",
                    "seeds": [42],
                    "authorization_approved": True,
                    # protocol_version intentionally omitted
                },
                "model": {"name": "gpt-4.1-mini", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with patch('experiments.run_causal.load_v1_tasks') as mock_load:
                mock_load.side_effect = AssertionError("Task loading should not be reached!")
                with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED.*protocol_version"):
                    run_causal(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_config_rejects_string_authorization(self):
        """Config must reject string values for authorization_approved."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_string_auth",
                    "phase": "dev",
                    "seeds": [42],
                    "authorization_approved": "false",  # String, not bool
                },
                "model": {"name": "mock", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            cfg = load_config(temp_path)
            # String "false" should be parsed as False, not True
            assert cfg.authorization_approved is False
        finally:
            Path(temp_path).unlink()

    def test_config_rejects_invalid_string_authorization(self):
        """Config must reject invalid string values for authorization_approved."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_invalid_auth",
                    "phase": "dev",
                    "seeds": [42],
                    "authorization_approved": "invalid",
                },
                "model": {"name": "mock", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="authorization_approved must be bool"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()
