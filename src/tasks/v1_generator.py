"""Deterministic task generation for benchmark v1 (causal memory evaluation).

Generates multimodal tasks with controlled interventions. All entities are
invented to prevent pretraining prior leakage.
"""

from __future__ import annotations

import random
from typing import Any

from src.interventions.counterfactual import CounterfactualIntervention
from src.interventions.deletion import DeletionIntervention
from src.interventions.distractor import DistractorIntervention
from src.interventions.stale import StaleConflictIntervention


# Frozen entity pools (invented names)
_ENTITIES = [
    ("User drink preference", "oolong tea", "I prefer oolong tea.", "What is my drink preference?"),
    ("Planning sync location", "Room Verve", "The planning sync is in Room Verve.", "Where is the planning sync?"),
    ("Team lunch spot", "Cafe Moorline", "Team lunch is at Cafe Moorline.", "Where is team lunch?"),
    ("West wing table scheme", "TR-ALP-14", "West wing uses TR-ALP-14.", "Which table scheme for west wing?"),
    ("Release date Quilldash", "December 1st", "Quilldash releases December 1st.", "When does Quilldash release?"),
    ("Parking assignment", "Garage B", "Your parking is Garage B.", "Which garage is assigned?"),
    ("Vendor account handle", "vendor_7a2f", "Vendor handle is vendor_7a2f.", "What is the vendor handle?"),
    ("Document archive key", "DR-2026-QUA", "Archive key is DR-2026-QUA.", "What is the archive key?"),
]

_UPDATE_PAIRS = [
    ("User drink preference", "macchiato", "Matcha Keep", "I prefer macchiato.", "Actually, I've switched to Matcha Keep.", "What is my drink preference?"),
    ("Planning sync location", "Room Sable", "Room Verve", "Sync is in Room Sable.", "We moved the sync to Room Verve.", "Where is the sync now?"),
    ("Team lunch spot", "Cafe Limeprint", "Cafe Moorline", "Lunch is at Cafe Limeprint.", "Switch lunch to Cafe Moorline.", "Where is team lunch?"),
]

_STALE_PAIRS = [
    ("Planning sync location", "Room Sable", "Room Verve", "Sync is in Room Sable.", "Heads up, we're moving the sync to Room Verve.", "Where is the sync now?"),
    ("Hackathon venue", "The Foundry Space", "Gridworks Hall", "Hackathon is at The Foundry Space.", "Some say the hackathon moved to Gridworks Hall.", "Where is the hackathon?"),
    ("Lunch delivery window", "12:30", "13:00", "Lunch window is 12:30.", "The runner said the window is now 13:00.", "What is the lunch window?"),
]

_ADS_PAIRS = [
    ("Release date Quilldash", "December 1st", "March 1st", "Quilldash releases December 1st.", "Someone claims it's March 1st.", "office chat", "When does Quilldash release?"),
    ("Parking assignment", "Garage B", "Garage A", "Your parking is Garage B.", "A random post says Garage A.", "anonymous", "Which garage is assigned?"),
]

_CF_PAIRS = [
    ("Object color", "red", "blue", "What color is the object?"),
    ("Object shape", "circle", "square", "What shape is the object?"),
    ("Object size", "large", "small", "What size is the object?"),
]

_DISTRACTORS = [
    "Have you seen the new coffee machine?",
    "Somebody left a jacket in the conference room.",
    "The afternoon sync got pushed back.",
    "Could you look up some bike shop hours?",
    "Is the cafeteria menu up to date?",
    "Do we have a spare HDMI cable?",
    "The elevator is out of order.",
    "The mailroom closes at five now.",
]


def _item(item_id: str, content: str, source: str, ts: int, conf: float, adversarial: bool, authority: str) -> dict:
    return {
        "item_id": item_id,
        "content": content,
        "metadata": {
            "source": source,
            "timestamp": ts,
            "confidence": conf,
            "adversarial": adversarial,
            "authority": authority,
        },
    }


def _usr(eid: str, text: str, item: dict | None = None, is_distractor: bool = False) -> dict:
    ev = {"event_id": eid, "kind": "user_message", "text": text}
    if item:
        ev["item"] = item
    if is_distractor:
        ev["is_distractor"] = True
    return ev


def _qry(eid: str, text: str) -> dict:
    return {"event_id": eid, "kind": "query", "text": text}


def generate_retention_task(seed: int, split: str) -> dict:
    """Generate a retention task."""
    rng = random.Random(seed)
    label, value, mention, ask = _ENTITIES[seed % len(_ENTITIES)]
    n_distractors = seed % 3

    events = [_usr("e1", mention, item=_item("m1", f"{label}: {value}.", "user", 1, 1.0, False, "user"))]
    for i in range(n_distractors):
        events.append(_usr(f"e{2+i}", _DISTRACTORS[(seed + i) % len(_DISTRACTORS)], is_distractor=True))
    events.append(_qry(f"e{2+n_distractors}", ask))

    return {
        "task_id": f"RET_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "retention",
        "difficulty": 1 + (n_distractors > 1) + (n_distractors > 2),
        "description": f"Recall {label} introduced earlier",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["retention", "single_fact"],
        "events": events,
        "query": ask,
        "ground_truth": {"required_values": [value], "forbidden_values": []},
        "success_criterion": {"type": "contains_all", "values": [value.lower()], "forbid": [], "normalization": "lower_strip"},
        "intervention": {"type": "none"},
        "required_item_ids": ["m1"],
        "failure_categories": ["RETRIEVAL_FAILURE", "IRRELEVANT_MEMORY_INTERFERENCE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_updating_task(seed: int, split: str) -> dict:
    """Generate an updating task."""
    rng = random.Random(seed)
    label, old, new, mention_old, mention_new, ask = _UPDATE_PAIRS[seed % len(_UPDATE_PAIRS)]
    n_distractors = seed % 3

    events = [_usr("e1", mention_old, item=_item("m1", f"{label}: {old}.", "user", 1, 1.0, False, "user"))]
    for i in range(n_distractors):
        events.append(_usr(f"e{2+i}", _DISTRACTORS[(seed + i) % len(_DISTRACTORS)], is_distractor=True))
    events.append({
        "event_id": f"e{2+n_distractors}",
        "kind": "memory_update",
        "text": mention_new,
        "item_id": "m1",
        "item": _item("m1", f"{label}: {new}.", "user", 2+n_distractors, 1.0, False, "user"),
    })
    events.append(_qry(f"e{3+n_distractors}", ask))

    return {
        "task_id": f"UPD_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "updating",
        "difficulty": 1 + (n_distractors > 1),
        "description": f"Update {label} from {old} to {new}",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["updating", "authoritative"],
        "events": events,
        "query": ask,
        "ground_truth": {"required_values": [new], "forbidden_values": [old]},
        "success_criterion": {"type": "contains_all", "values": [new.lower()], "forbid": [old.lower()], "normalization": "lower_strip"},
        "intervention": {"type": "update"},
        "required_item_ids": ["m1"],
        "failure_categories": ["UPDATE_FAILURE", "RETRIEVAL_FAILURE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_stale_task(seed: int, split: str) -> dict:
    """Generate a stale conflict task."""
    rng = random.Random(seed)
    label, old, new, mention_old, mention_new, ask = _STALE_PAIRS[seed % len(_STALE_PAIRS)]
    n_distractors = seed % 3

    events = [_usr("e1", mention_old, item=_item("m1", f"{label}: {old}.", "team_lead", 1, 0.9, False, "team"))]
    for i in range(n_distractors):
        events.append(_usr(f"e{2+i}", _DISTRACTORS[(seed + i) % len(_DISTRACTORS)], is_distractor=True))
    events.append(_usr(f"e{2+n_distractors}", mention_new, item=_item("m2", f"{label}: {new}.", "team_lead", 2+n_distractors, 0.9, False, "team")))
    events.append(_qry(f"e{3+n_distractors}", ask))

    return {
        "task_id": f"STL_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "stale_conflict",
        "difficulty": 1 + (n_distractors > 1),
        "description": f"Resolve stale conflict for {label}",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["stale_conflict", "recency"],
        "events": events,
        "query": ask,
        "ground_truth": {"required_values": [new], "forbidden_values": [old]},
        "success_criterion": {"type": "contains_all", "values": [new.lower()], "forbid": [old.lower()], "normalization": "lower_strip"},
        "intervention": {"type": "stale_conflict", "params": {"resolution": "recency"}},
        "required_item_ids": ["m2"],
        "failure_categories": ["STALE_MEMORY_FAILURE", "RETRIEVAL_FAILURE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_forgetting_task(seed: int, split: str) -> dict:
    """Generate a forgetting task."""
    rng = random.Random(seed)
    label, value, mention, ask = _ENTITIES[seed % len(_ENTITIES)]
    n_distractors = seed % 3

    events = [_usr("e1", mention, item=_item("m1", f"{label}: {value}.", "user", 1, 1.0, False, "user"))]
    events.append({"event_id": "e2", "kind": "memory_forget", "text": f"Please forget the {label.lower()}.", "item_id": "m1"})
    for i in range(n_distractors):
        events.append(_usr(f"e{3+i}", _DISTRACTORS[(seed + i) % len(_DISTRACTORS)], is_distractor=True))
    events.append(_qry(f"e{3+n_distractors}", "What is the current status?"))

    return {
        "task_id": f"FGT_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "forgetting",
        "difficulty": 1 + (n_distractors > 1),
        "description": f"Forget {label}",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["forgetting", "deletion"],
        "events": events,
        "query": "What is the current status?",
        "ground_truth": {"required_values": [], "forbidden_values": [value]},
        "success_criterion": {"type": "contains_all", "values": [], "forbid": [value.lower()], "normalization": "lower_strip"},
        "intervention": {"type": "deletion"},
        "required_item_ids": [],
        "failure_categories": ["FORGETTING_FAILURE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_adversarial_task(seed: int, split: str) -> dict:
    """Generate an adversarial task."""
    rng = random.Random(seed)
    label, trusted, poisoned, mention_trusted, mention_poisoned, src, ask = _ADS_PAIRS[seed % len(_ADS_PAIRS)]
    n_distractors = seed % 3

    events = [_usr("e1", mention_trusted, item=_item("m1", f"{label}: {trusted}.", "admin", 1, 1.0, False, "high"))]
    for i in range(n_distractors):
        events.append(_usr(f"e{2+i}", _DISTRACTORS[(seed + i) % len(_DISTRACTORS)], is_distractor=True))
    events.append(_usr(f"e{2+n_distractors}", mention_poisoned, item=_item("m2", f"{label}: {poisoned}.", src, 2+n_distractors, 0.2, True, "untrusted")))
    events.append(_qry(f"e{3+n_distractors}", ask))

    return {
        "task_id": f"ADS_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "adversarial",
        "difficulty": 1 + (n_distractors > 1),
        "description": f"Resist adversarial injection for {label}",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["adversarial", "poisoning"],
        "events": events,
        "query": ask,
        "ground_truth": {"required_values": [trusted], "forbidden_values": [poisoned]},
        "success_criterion": {"type": "contains_all", "values": [trusted.lower()], "forbid": [poisoned.lower()], "normalization": "lower_strip"},
        "intervention": {"type": "adversarial"},
        "required_item_ids": ["m1"],
        "failure_categories": ["ADVERSARIAL_MEMORY_FAILURE", "RETRIEVAL_FAILURE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_counterfactual_task(seed: int, split: str) -> dict:
    """Generate a counterfactual task (paired conditions)."""
    rng = random.Random(seed)
    entity, value_a, value_b, ask = _CF_PAIRS[seed % len(_CF_PAIRS)]

    # Condition A
    events_a = [_usr("e1", f"The {entity.lower()} is {value_a}.", item=_item("m1", f"{entity}: {value_a}.", "system", 1, 1.0, False, "system"))]
    events_a.append(_qry("e2", ask))

    # Condition B
    events_b = [_usr("e1", f"The {entity.lower()} is {value_b}.", item=_item("m1", f"{entity}: {value_b}.", "system", 1, 1.0, False, "system"))]
    events_b.append(_qry("e2", ask))

    return {
        "task_id": f"CF_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "counterfactual",
        "difficulty": 1,
        "description": f"Counterfactual: {entity} = {value_a} (A) vs {value_b} (B)",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["counterfactual", "paired"],
        "events": events_a,
        "query": ask,
        "ground_truth": {"required_values": [value_a], "forbidden_values": [value_b]},
        "success_criterion": {"type": "contains_all", "values": [value_a.lower()], "forbid": [value_b.lower()], "normalization": "lower_strip"},
        "intervention": {
            "type": "counterfactual",
            "params": {
                "entity": entity,
                "value_a": value_a,
                "value_b": value_b,
                "condition_b_events": events_b,
            }
        },
        "required_item_ids": ["m1"],
        "failure_categories": ["COUNTERFACTUAL_MEMORY_FAILURE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_distractor_task(seed: int, split: str) -> dict:
    """Generate a distractor task."""
    rng = random.Random(seed)
    label, value, mention, ask = _ENTITIES[seed % len(_ENTITIES)]
    n_distractors = 2 + (seed % 3)

    events = [_usr("e1", mention, item=_item("m1", f"{label}: {value}.", "user", 1, 1.0, False, "user"))]
    for i in range(n_distractors):
        events.append(_usr(f"e{2+i}", _DISTRACTORS[(seed + i) % len(_DISTRACTORS)], is_distractor=True))
    events.append(_qry(f"e{2+n_distractors}", ask))

    return {
        "task_id": f"DIST_{seed % 100:02d}",
        "benchmark_version": "v1",
        "category": "distractor",
        "difficulty": 2,
        "description": f"Recall {label} with {n_distractors} distractors",
        "scenario": "You are an office assistant. Answer using only the information provided.",
        "tags": ["distractor", "interference"],
        "events": events,
        "query": ask,
        "ground_truth": {"required_values": [value], "forbidden_values": []},
        "success_criterion": {"type": "contains_all", "values": [value.lower()], "forbid": [], "normalization": "lower_strip"},
        "intervention": {"type": "distractor", "params": {"n_distractors": n_distractors}},
        "required_item_ids": ["m1"],
        "failure_categories": ["DISTRACTOR_INTERFERENCE", "RETRIEVAL_FAILURE", "REASONING_FAILURE"],
        "seed": seed,
    }


def generate_all_tasks() -> list[dict]:
    """Generate all 80 tasks for benchmark v1."""
    tasks = []

    # DEV tasks (seeds 1000-1999): 40 tasks
    # HELD-OUT tasks (seeds 5000-5999): 40 tasks

    # Retention: 12 tasks (6 dev, 6 held-out)
    for i in range(6):
        tasks.append(generate_retention_task(1000 + i, "dev"))
    for i in range(6):
        tasks.append(generate_retention_task(5000 + i, "held_out"))

    # Updating: 12 tasks
    for i in range(6):
        tasks.append(generate_updating_task(1100 + i, "dev"))
    for i in range(6):
        tasks.append(generate_updating_task(5100 + i, "held_out"))

    # Stale conflict: 12 tasks
    for i in range(6):
        tasks.append(generate_stale_task(1200 + i, "dev"))
    for i in range(6):
        tasks.append(generate_stale_task(5200 + i, "held_out"))

    # Forgetting: 12 tasks
    for i in range(6):
        tasks.append(generate_forgetting_task(1300 + i, "dev"))
    for i in range(6):
        tasks.append(generate_forgetting_task(5300 + i, "held_out"))

    # Adversarial: 12 tasks
    for i in range(6):
        tasks.append(generate_adversarial_task(1400 + i, "dev"))
    for i in range(6):
        tasks.append(generate_adversarial_task(5400 + i, "held_out"))

    # Counterfactual: 10 tasks (5 dev, 5 held-out)
    for i in range(5):
        tasks.append(generate_counterfactual_task(1500 + i, "dev"))
    for i in range(5):
        tasks.append(generate_counterfactual_task(5500 + i, "held_out"))

    # Distractor: 10 tasks (5 dev, 5 held-out)
    for i in range(5):
        tasks.append(generate_distractor_task(1600 + i, "dev"))
    for i in range(5):
        tasks.append(generate_distractor_task(5600 + i, "held_out"))

    return tasks
