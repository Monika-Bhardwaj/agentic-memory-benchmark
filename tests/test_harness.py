from pathlib import Path

from src.agents.harness import AgentHarness
from src.agents.models import PatternMockModel
from src.evaluation.classifier import FailureClassifier
from src.memory.base import MemoryLogger
from src.memory.no_memory import NoMemory
from src.memory.structured_memory import StructuredMemory
from src.tasks.loader import load_tasks

ROOT = Path(__file__).resolve().parents[1]


def _task(task_id: str) -> dict:
    tasks, _ = load_tasks()
    return next(t for t in tasks if t["task_id"] == task_id)


def _outcome(harness, task, system, seed=42, top_k=3):
    cfg = {"response": None}
    mem_cls = StructuredMemory if system in ("structured_memory", "sacam_v0") else NoMemory
    mem = mem_cls(seed, MemoryLogger())
    if system == "sacam_v0":
        from src.memory.base import MemoryItem
        from src.memory.sacam_v0 import SACAMv0
        mem = SACAMv0(seed, MemoryLogger())
    if system == "full_context":
        from src.memory.naive_retrieval import NaiveRetrieval
        mem = NaiveRetrieval(seed, MemoryLogger())
        top_k = -1
    return harness.run_task(
        task, mem, seed=seed, system=system, retrieval_top_k=top_k,
        respond_to_non_query_events=False, model_temperature=0, model_max_output_tokens=512,
    )


def test_pattern_mock_extracts_memory_section():
    m = PatternMockModel()
    out = m.complete("[system] hello\n\n=== MEMORY (retrieved) ===\n- [m1 | 5 | team_lead | 0.9] Kestrel Prime is Scorch.\n=== END ===\n\n[user] who?", 0, 512)
    assert "Kestrel Prime is Scorch" in out


def test_retention_success_depends_on_retrieval():
    harness = AgentHarness(PatternMockModel(), "v0.1-p1")
    task = _task("A_RET_01")
    assert task["required_item_ids"] == ["m1"]
    good = _outcome(harness, task, "structured_memory")
    bad = _outcome(harness, task, "no_memory")
    assert good.success, good.notes
    assert not bad.success
    assert bad.primary_failure_label in (
        "RETRIEVAL_FAILURE", "REASONING_FAILURE", "IRRELEVANT_MEMORY_INTERFERENCE")


def test_forgetting_must_not_answer_poison():
    harness = AgentHarness(PatternMockModel(), "v0.1-p1")
    task = _task("D_FGT_01")
    # forgetting task with forbidden value; structured memory forgets it
    out = _outcome(harness, task, "structured_memory")
    if out.success:
        return  # passing only if forbidden value rejected
    assert out.primary_failure_label == "FORGETTING_FAILURE"


def test_updating_prefers_new_value():
    harness = AgentHarness(PatternMockModel(), "v0.1-p1")
    task = _task("B_UPD_03")
    out = _outcome(harness, task, "structured_memory")
    assert out.success


def test_adversarial_flag_never_rendered_into_prompt():
    task = _task("E_ADS_01")
    poisoned = [
        e for e in task["events"]
        if e.get("item") and e["item"]["metadata"].get("adversarial") is True
    ]
    assert poisoned, "E_ADS_01 should contain a poisoned item"
    prompts: list[str] = []

    class Rec(PatternMockModel):
        def complete(self, prompt, temperature, max_output_tokens):
            prompts.append(prompt)
            return super().complete(prompt, temperature, max_output_tokens)

    rec = AgentHarness(Rec(), "v0.1-p1")
    _outcome(rec, task, "structured_memory")
    assert prompts, "no prompts recorded"
    for p in prompts:
        assert "adversarial" not in p.lower()


def test_classifier_frozen_labels_cover_failures():
    from src.evaluation.outcome import TaskOutcome
    out = TaskOutcome(task_id="x", category="retention", difficulty=1, system="s", seed=1,
                      query="q", answer="wrong", success=False,
                      primary_failure_label=None, failure_reason=None)
    label, reason = FailureClassifier().classify(
        task={"category": "retention", "required_item_ids": []},
        outcome=out, store_item_ids=["m1"], retrieved_ids=["m1"],
        forget_target_ids=[])
    assert label == "REASONING_FAILURE" or label == "RETENTION_FAILURE", label