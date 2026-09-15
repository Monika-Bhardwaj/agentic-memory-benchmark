from pathlib import Path

import pytest

from src.config import ExperimentConfig, load_config, render_normalized_config
from src.metrics.metrics import aggregate_tsr, category_success_rates, failure_category_counts

ROOT = Path(__file__).resolve().parents[1]


def test_load_smoke_config():
    cfg = load_config(ROOT / "configs" / "smoke.yaml")
    assert cfg.name == "sacam_smoke_v01"
    assert len(cfg.tasks_subset) == 8
    assert cfg.systems == ["no_memory", "naive_retrieval", "structured_memory", "sacam_v0", "full_context"]


def test_config_hash_deterministic():
    cfg1 = load_config(ROOT / "configs" / "smoke.yaml")
    cfg2 = load_config(ROOT / "configs" / "smoke.yaml")
    assert cfg1.hash() == cfg2.hash()
    assert render_normalized_config(cfg1) == render_normalized_config(cfg2)


def test_bad_config_missing_block(tmp_path):
    p = tmp_path / "bad.yaml"
    p.write_text("model:\n  name: mock_pattern_reader\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(p)


def test_metrics_pure():
    class O:
        def __init__(self, ok, cat):
            self.success = ok; self.category = cat; self.system = "s"; self.seed = 1
            self.primary_failure_label = None
            self.required_ids = []; self.retrieved_ids = []
    cells = [O(True, "retention"), O(False, "retention")]
    agg = aggregate_tsr(cells)
    assert agg["per_seed"]["s/1"] == 0.5
    cat = category_success_rates(cells)
    assert cat["retention"]["success_rate"] == 0.5
    counts = failure_category_counts([O(False, "retention")])
    assert counts["ALL_FAILURES"] == 1