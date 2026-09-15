"""Agent harness: executes one task session against the frozen event stream.

Controlled differences only: which memory items are surfaced (rank/composition from
the configured system) and, for ``full_context``, the top-k window (=-1 → store size).
The renderer/prompt shape is identical across systems; the memory section format is
the same for every system (docs/experiment_protocol.md §2 Renderer policy).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.agents.models import MEMORY_END, MEMORY_MARKER, ModelClient
from src.evaluation.classifier import FailureClassifier
from src.evaluation.evaluator import apply_success_criterion
from src.evaluation.outcome import TaskOutcome
from src.memory.base import Memory, MemoryItem, MemoryLogger, RetrievedItem


@dataclass
class SessionRecord:
    system: str
    seed: int
    task_id: str
    transcripts: list[dict[str, Any]] = field(default_factory=list)
    outcome: TaskOutcome | None = None


def _render_memory_section(items: list[RetrievedItem]) -> str:
    if not items:
        return ""
    lines = []
    for it in items:
        meta = it.metadata
        lines.append(
            f"- [{it.item_id} | {meta.get('timestamp', '?')} | {meta.get('source', '?')} | "
            f"{meta.get('confidence', '?')}] {it.content}"
        )
    return f"\n{MEMORY_MARKER}\n" + "\n".join(lines) + f"\n{MEMORY_END}\n"


def _estimate_tokens(text: str) -> int:
    return max(0, len(text) // 4)


class AgentHarness:
    def __init__(self, model: ModelClient, prompt_version: str) -> None:
        self.model = model
        self.prompt_version = prompt_version
        self._classifier = FailureClassifier()

    def run_task(
        self,
        task: dict,
        memory: Memory,
        *,
        seed: int,
        system: str,
        retrieval_top_k: int,
        respond_to_non_query_events: bool,
        model_temperature: float,
        model_max_output_tokens: int,
    ) -> TaskOutcome:
        logger = MemoryLogger()
        events = task["events"]
        transcript: list[dict[str, Any]] = []
        final_answer: str | None = None
        infra_error = False
        retrieved_ids: list[str] = []
        memory_section_text = ""
        memory_section_tokens = 0

        for event in events:
            kind = event["kind"]
            event_text = event.get("text", "")
            if kind == "query":
                top_k = retrieval_top_k if retrieval_top_k >= 0 else len(memory.inspect())
                items = memory.retrieve(event_text, top_k)
                retrieved_ids = [r.item_id for r in items]
                memory_section_text = _render_memory_section(items)
                memory_section_tokens = _estimate_tokens(memory_section_text)

            prompt = self._build_prompt(task["scenario"], event_text, memory_section_text if kind == "query" else "")
            response: str | None = None
            model_meta: dict[str, Any] = {}
            if kind == "query" or respond_to_non_query_events:
                try:
                    response = self.model.complete(
                        prompt,
                        temperature=model_temperature,
                        max_output_tokens=model_max_output_tokens,
                    )
                except Exception as exc:  # noqa: BLE001 - infra failures are recorded, never swallowed
                    infra_error = True
                    response = None
                    model_meta = {"error": f"{type(exc).__name__}: {exc}"}
                model_meta.update(self.model.metadata())
            transcript.append({
                "event_id": event["event_id"],
                "kind": kind,
                "text": event_text,
                "prompt": prompt,
                "response": response,
                "infra_error": infra_error,
            })

            if kind == "user_message" and event.get("item"):
                memory.add(_as_item(event["item"]))
            elif kind == "memory_update":
                memory.update(event["item_id"], _as_item(event["item"]))
            elif kind == "memory_forget":
                memory.forget(event["item_id"])

            if kind == "query":
                final_answer = response

        store_items = memory.inspect()
        success, detail = apply_success_criterion(task["success_criterion"], final_answer)
        outcome = TaskOutcome(
            task_id=task["task_id"],
            category=task["category"],
            difficulty=task["difficulty"],
            system=system,
            seed=seed,
            query=task["query"],
            answer=final_answer,
            success=success,
            primary_failure_label=None,
            failure_reason=None,
            retrieved_ids=retrieved_ids,
            required_ids=list(task.get("required_item_ids", [])),
            required_in_store=all(
                rid in [it.item_id for it in store_items] for rid in task.get("required_item_ids", [])
            ),
            required_relevant_retrieved=all(
                rid in retrieved_ids for rid in task.get("required_item_ids", [])
            ),
            store_size_at_query=len(store_items),
            memory_section_tokens_est=memory_section_tokens,
            memory_section_chars=len(memory_section_text),
            model_metadata=model_meta,
            notes=[detail["reason"]] if detail.get("reason") else [],
        )
        self._classifier.apply(
            task,
            outcome,
            store_item_ids=[it.item_id for it in store_items],
            forget_target_ids=logger.forget_target_ids(),
            infra_error=infra_error,
        )
        outcome.notes.append(f"avg_prompt_chars={_estimate_tokens('') or 0}")
        outcome.notes = [n for n in outcome.notes if n != "avg_prompt_chars=0"]
        return outcome

    def _build_prompt(self, scenario: str, event_text: str, memory_section: str) -> str:
        parts = [f"[system] {scenario}"]
        if memory_section:
            parts.append(memory_section)
        parts.append(f"[user] {event_text}")
        return "\n\n".join(parts)


def _as_item(item: dict) -> MemoryItem:
    return MemoryItem(item_id=item["item_id"], content=item["content"], metadata=item.get("metadata", {}))