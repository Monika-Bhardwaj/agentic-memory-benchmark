import json
from pathlib import Path

import pytest

from src.tasks.loader import load_tasks
from src.tasks.validation import validate_task

BENCHMARK_DIR = Path(__file__).resolve().parents[1] / "benchmark" / "v0"


def _fixture(name: str) -> dict:
    with open(BENCHMARK_DIR / "fixtures" / name, encoding="utf-8") as fh:
        return json.load(fh)


def _task_rows() -> list[dict]:
    tasks, _ = load_tasks()
    return tasks


def test_fixtures_validate():
    for name in ["A_RET_FX01.json", "B_UPD_FX01.json", "C_STL_FX01.json", "D_FGT_FX01.json", "E_ADS_FX01.json"]:
        t = _fixture(name)
        errs = validate_task(t)
        assert not errs, f"{name}: {errs}"


def test_all_generated_tasks_validate():
    tasks, _ = load_tasks()
    assert len(tasks) == 40
    for t in tasks:
        errs = validate_task(t)
        assert not errs, f"{t['task_id']}: {errs}"


def test_category_counts():
    tasks, _ = load_tasks()
    counts = {}
    for t in tasks:
        counts[t["category"]] = counts.get(t["category"], 0) + 1
    assert counts == {"retention": 8, "updating": 8, "stale_conflict": 8, "forgetting": 8, "adversarial": 8}


def test_benchmark_hash_is_frozen():
    tasks, h = load_tasks()
    assert h == "f78a3491c9ee969d09e862cd89bb648b93df9f8b5c21ca989cd15667d3389367"


def test_query_is_last_and_only_query():
    for t in _task_rows():
        kinds = [e["kind"] for e in t["events"]]
        assert kinds.count("query") == 1
        assert kinds[-1] == "query"


def test_seeds_are_unique():
    tasks, _ = load_tasks()
    seeds = [t["seed"] for t in tasks]
    assert len(seeds) == len(set(seeds))