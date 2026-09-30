"""Generate and freeze benchmark v1 tasks.

Usage::

    python experiments/generate_v1_benchmark.py

Generates all 80 tasks, validates them, writes to benchmark/v1/tasks.jsonl,
and prints the benchmark hash.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tasks.v1_generator import generate_all_tasks
from src.tasks.v1_validation import validate_v1_task
from src.utils.hashing import file_sha256


def main() -> None:
    print("Generating benchmark v1 tasks...")
    tasks = generate_all_tasks()

    # Validate all tasks
    print(f"Validating {len(tasks)} tasks...")
    errors = []
    for task in tasks:
        task_errors = validate_v1_task(task)
        if task_errors:
            errors.append((task["task_id"], task_errors))

    if errors:
        print(f"VALIDATION ERRORS ({len(errors)} tasks):")
        for task_id, task_errors in errors:
            print(f"  {task_id}: {task_errors}")
        sys.exit(1)

    # Check category distribution
    from collections import Counter
    categories = Counter(t["category"] for t in tasks)
    print(f"Category distribution: {dict(categories)}")

    # Check split distribution
    dev_tasks = [t for t in tasks if t["seed"] < 5000]
    held_out_tasks = [t for t in tasks if t["seed"] >= 5000]
    print(f"DEV tasks: {len(dev_tasks)}, HELD-OUT tasks: {len(held_out_tasks)}")

    # Write to file
    output_path = ROOT / "benchmark" / "v1" / "tasks.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        for task in tasks:
            fh.write(json.dumps(task, ensure_ascii=False) + "\n")

    # Compute hash
    benchmark_hash = file_sha256(output_path)
    print(f"\nBenchmark v1 generated: {output_path}")
    print(f"Benchmark hash: {benchmark_hash}")
    print(f"Total tasks: {len(tasks)}")

    # Update manifest
    manifest_path = ROOT / "benchmark" / "v1" / "task_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest["status"] = "generated"
    manifest["benchmark_hash"] = benchmark_hash
    manifest["tasks"] = [
        {
            "task_id": t["task_id"],
            "category": t["category"],
            "difficulty": t["difficulty"],
            "seed": t["seed"],
            "split": "dev" if t["seed"] < 5000 else "held_out",
        }
        for t in tasks
    ]
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    print(f"Manifest updated: {manifest_path}")


if __name__ == "__main__":
    main()
