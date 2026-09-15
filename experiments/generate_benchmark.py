"""Generate the frozen benchmark file from the manifest + templates.

Run once, commit the output, then treat ``tasks.jsonl`` as immutable::

    python experiments/generate_benchmark.py

The output is committed alongside this script; re-running produces identical content
for identical manifest + generator.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tasks.generator import generate_all
from src.tasks.validation import validate_task
from src.utils.hashing import file_sha256


def main() -> None:
    manifest_path = ROOT / "benchmark" / "v0" / "task_manifest.json"
    tasks_path = ROOT / "benchmark" / "v0" / "tasks.jsonl"

    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)

    rows = manifest["tasks"]
    print(f"Generating {len(rows)} tasks from manifest...", flush=True)
    tasks = generate_all(rows)

    all_errors: list[str] = []
    for t in tasks:
        errs = validate_task(t)
        if errs:
            all_errors.append(f"{t['task_id']}: {errs}")
    if all_errors:
        print("VALIDATION ERRORS:")
        for err in all_errors:
            print("  ", err)
        sys.exit(1)

    with open(tasks_path, "w", encoding="utf-8") as fh:
        for t in tasks:
            fh.write(json.dumps(t, ensure_ascii=False, sort_keys=True) + "\n")

    h = file_sha256(tasks_path)
    print(f"Written {tasks_path}  ({len(tasks)} tasks)")
    print(f"benchmark_hash = {h}")


if __name__ == "__main__":
    main()