"""Tests for protected run fail-closed gate.

Verifies that the Python runner rejects protected runs when authorization
is false or missing, BEFORE loading tasks or constructing the model.
"""

import pytest
import sys
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

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
            with pytest.raises(ValueError, match="authorization_approved must be a Boolean"):
                load_config(temp_path)
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
            with pytest.raises(ValueError, match="authorization_approved must be a Boolean"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_config_rejects_quoted_true_authorization(self):
        """Config must reject quoted string 'true' for authorization_approved."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_quoted_true",
                    "phase": "dev",
                    "seeds": [42],
                    "authorization_approved": "true",  # Quoted string, not bool
                },
                "model": {"name": "mock", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="authorization_approved must be a Boolean"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_config_rejects_quoted_false_authorization(self):
        """Config must reject quoted string 'false' for authorization_approved."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_quoted_false",
                    "phase": "dev",
                    "seeds": [42],
                    "authorization_approved": "false",  # Quoted string, not bool
                },
                "model": {"name": "mock", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="authorization_approved must be a Boolean"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_config_rejects_integer_authorization(self):
        """Config must reject integer values for authorization_approved."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_int_auth",
                    "phase": "dev",
                    "seeds": [42],
                    "authorization_approved": 1,  # Integer, not bool
                },
                "model": {"name": "mock", "temperature": 0, "max_output_tokens": 512},
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="authorization_approved must be a Boolean"):
                load_config(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_runner_rejects_seed_override_for_protected(self):
        """Protected run with seed override must be rejected."""
        from experiments.run_causal import run_causal

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_seed_override",
                    "benchmark_version": "v1",
                    "phase": "protected",
                    "seeds": [42],
                    "authorization_approved": True,
                    "protocol_version": "v0.2",
                },
                "model": {
                    "name": "gpt-4.1-mini",
                    "provider": "openai",
                    "snapshot": "gpt-4.1-mini-2025-04-14",
                    "temperature": 0,
                    "max_output_tokens": 512,
                },
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with patch('experiments.run_causal.load_v1_tasks') as mock_load:
                mock_load.side_effect = AssertionError("Task loading should not be reached!")
                with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED.*overrides"):
                    run_causal(temp_path, seed_override=99)
        finally:
            Path(temp_path).unlink()

    def test_runner_rejects_system_override_for_protected(self):
        """Protected run with system override must be rejected."""
        from experiments.run_causal import run_causal

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_content = {
                "experiment": {
                    "name": "test_system_override",
                    "benchmark_version": "v1",
                    "phase": "protected",
                    "seeds": [42],
                    "authorization_approved": True,
                    "protocol_version": "v0.2",
                },
                "model": {
                    "name": "gpt-4.1-mini",
                    "provider": "openai",
                    "snapshot": "gpt-4.1-mini-2025-04-14",
                    "temperature": 0,
                    "max_output_tokens": 512,
                },
                "memory": {"retrieval_top_k": 3, "memory_budget_items": 512},
                "evaluation": {"primary_metric": "tsr", "mme": 0.05},
                "harness": {"max_retries": 0},
            }
            yaml.dump(config_content, f)
            temp_path = f.name

        try:
            with patch('experiments.run_causal.load_v1_tasks') as mock_load:
                mock_load.side_effect = AssertionError("Task loading should not be reached!")
                with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED.*overrides"):
                    run_causal(temp_path, system_override="no_memory")
        finally:
            Path(temp_path).unlink()

    def test_model_adapter_uses_snapshot(self):
        """Model adapter must use the snapshot field, not the moving alias."""
        from src.agents.models import build_model

        cfg_model = {
            "name": "gpt-4.1-mini",
            "provider": "openai",
            "snapshot": "gpt-4.1-mini-2025-04-14",
            "temperature": 0,
            "max_output_tokens": 512,
        }
        harness_cfg = {"timeout_seconds": 60, "max_retries": 0}

        # Mock LiveLLMClient to capture the model argument
        with patch('src.agents.models.LiveLLMClient') as mock_client:
            mock_client.return_value = MagicMock()
            build_model(cfg_model, harness_cfg)
            # Verify LiveLLMClient was called with the snapshot, not the alias
            mock_client.assert_called_once()
            call_kwargs = mock_client.call_args
            assert call_kwargs.kwargs.get('model') == 'gpt-4.1-mini-2025-04-14' or \
                   (call_kwargs.args and call_kwargs.args[0] == 'gpt-4.1-mini-2025-04-14')

    def test_model_adapter_rejects_wrong_provider(self):
        """Model adapter must reject non-openai providers."""
        from src.agents.models import build_model

        cfg_model = {
            "name": "gpt-4.1-mini",
            "provider": "other_provider",
            "snapshot": "gpt-4.1-mini-2025-04-14",
            "temperature": 0,
            "max_output_tokens": 512,
        }
        harness_cfg = {"timeout_seconds": 60, "max_retries": 0}

        with pytest.raises(RuntimeError, match="provider must be 'openai'"):
            build_model(cfg_model, harness_cfg)

    def test_model_adapter_binds_fixed_endpoint(self):
        """Model adapter must use fixed endpoint, not env substitution."""
        from src.agents.models import build_model

        cfg_model = {
            "name": "gpt-4.1-mini",
            "provider": "openai",
            "snapshot": "gpt-4.1-mini-2025-04-14",
            "temperature": 0,
            "max_output_tokens": 512,
        }
        harness_cfg = {"timeout_seconds": 60, "max_retries": 0}

        # Set an env variable that would override the endpoint
        import os
        old_url = os.environ.get("LLM_BASE_URL")
        os.environ["LLM_BASE_URL"] = "https://malicious-endpoint.example.com/v1"
        try:
            with patch('src.agents.models.LiveLLMClient') as mock_client:
                mock_client.return_value = MagicMock()
                build_model(cfg_model, harness_cfg)
                # Verify LiveLLMClient was called with fixed base_url
                call_kwargs = mock_client.call_args.kwargs
                assert call_kwargs.get('base_url') == 'https://api.openai.com/v1'
        finally:
            if old_url is None:
                os.environ.pop("LLM_BASE_URL", None)
            else:
                os.environ["LLM_BASE_URL"] = old_url
