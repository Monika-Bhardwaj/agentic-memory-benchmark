"""Benchmark v1 task loader.

Loads the frozen v1 task set with multimodal and intervention support.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.utils.hashing import file_sha256


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_V1_TASKS_PATH = ROOT / "benchmark" / "v1" / "tasks.jsonl"


class BenchmarkLoadError(RuntimeError):
    pass


def load_v1_tasks(path: Path | None = None) -> tuple[list[dict], str]:
    """Return (tasks, benchmark_hash) for v1 tasks."""
    path = Path(path) if path else DEFAULT_V1_TASKS_PATH
    if not path.exists():
        raise BenchmarkLoadError(f"v1 benchmark file not found: {path}")
    tasks = []
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                tasks.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise BenchmarkLoadError(f"line {line_no} invalid JSON: {exc}") from exc
    if not tasks:
        raise BenchmarkLoadError("v1 benchmark file is empty")
    return tasks, file_sha256(path)


def generate_and_save_v1_tasks(output_path: Path | None = None) -> str:
    """Generate all v1 tasks and save to tasks.jsonl. Returns benchmark hash."""
    from src.tasks.v1_generator import generate_all_tasks

    tasks = generate_all_tasks()
    output_path = Path(output_path) if output_path else DEFAULT_V1_TASKS_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as fh:
        for task in tasks:
            fh.write(json.dumps(task, ensure_ascii=False) + "\n")

    return file_sha256(output_path)
