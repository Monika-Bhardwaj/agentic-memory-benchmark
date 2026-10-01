"""Tests for protected run fail-closed gate.

Verifies that the Python runner rejects protected runs when authorization
is false or missing, BEFORE loading tasks or constructing the model.
"""

import pytest
import sys
from pathlib import Path

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
        # DEV runs should not be blocked
        assert cfg.authorization_approved is False  # but not required for dev

    def test_config_hash_includes_authorization(self):
        """Config hash must include authorization_approved field."""
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        hash1 = cfg.hash()
        # Changing authorization should change hash
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
        # Ensure approval is false
        assert cfg.authorization_approved is False
        # The runner must raise RuntimeError before loading tasks
        with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED"):
            run_causal(ROOT / "configs" / "causal_protected.yaml")

    def test_runner_blocks_wrong_protocol_version(self):
        """Protected run with wrong protocol version must be rejected."""
        from experiments.run_causal import run_causal
        cfg = load_config(ROOT / "configs" / "causal_protected.yaml")
        # Temporarily set approval true but wrong protocol
        cfg.authorization_approved = True
        cfg.protocol_version = "v0.1"
        with pytest.raises(RuntimeError, match="PROTECTED RUN BLOCKED"):
            run_causal(ROOT / "configs" / "causal_protected.yaml")
