"""Frozen benchmark loader. Loads the committed, hashed tasks file only."""

from __future__ import annotations

import json
from pathlib import Path

from src.utils.hashing import file_sha256

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TASKS_PATH = ROOT / "benchmark" / "v0" / "tasks.jsonl"


class BenchmarkLoadError(RuntimeError):
    pass


def load_tasks(path: Path | None = None) -> tuple[list[dict], str]:
    """Return (tasks, benchmark_hash). All tasks must validate."""
    path = Path(path) if path else DEFAULT_TASKS_PATH
    if not path.exists():
        raise BenchmarkLoadError(f"benchmark file not found: {path}")
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
        raise BenchmarkLoadError("benchmark file is empty")
    return tasks, file_sha256(path)