"""Deterministic task generation for benchmark v0.1.

Guarantees
----------
* Purely deterministic: for a given manifest row, and the frozen pools/templates below,
  the generated task is a constant (verified by tests).
* Follows the canonical ``LABEL: VALUE.`` content convention (SPEC.md §4).
* All entities are invented (no pretraining priors can supply answers).
* Distractors are drawn without replacement within a task.

The generated ``tasks.jsonl`` — not this generator — is the authority for experiments.
This module exists for provenance and for creating future benchmark versions.
"""

from __future__ import annotations

import random
from typing import Callable

from src.tasks.validation import validate_task

SCENARIO = (
    "You are an office assistant for a small startup called Ferric Labs. "
    "Users give you information over time and occasionally ask questions. "
    "Answer precisely and completely using only the information provided "
    "in this conversation."
)

DISTRACTORS = [
    "Have you seen the new coffee machine on the third floor?",
    "Somebody left a jacket in the conference room.",
    "The afternoon sync got pushed back by an hour.",
    "Could you look up some bike shop hours for me?",
    "Is the cafeteria menu up to date this week?",
    "Do we have a spare HDMI cable in the supply closet?",
    "The elevator on the eastern stairwell is out of order.",
    "Can you confirm which floors reachable via the service door?",
    "The mailroom closes at five now.",
    "Someone asked about the printer paper order.",
    "Did anyone book the glass meeting room for Thursday?",
    "The fire drill is scheduled for next Wednesday morning.",
    "A plant fell over in the break room and needs a new pot.",
    "The Wi-Fi was slow in the north wing this morning.",
    "Are the parking stickers for the overflow lot ready?",
    "The intern is looking for the shared drive permissions.",
    "Can you add a reminder about the quarterly offsite?",
    "The thermostat in office 3C is stuck at 28 degrees.",
    "Who has the keys to the storage cabinet?",
    "The chairs in the lounge were reupholstered last week.",
    "An unclaimed delivery arrived at the front desk.",
    "The whiteboard markers keep going missing.",
    "Is the espresso machine being serviced today?",
    "Someone wants the quarterly report printed in color.",
    "The visitor badges need to be restocked.",
    "Can we move the standing desk between floors?",
    "The window blinds in the boardroom are broken.",
    "There is a noise complaint about the server room fan.",
    "The receptionist wants the rota republished.",
    "The plant deliveries are now biweekly instead of weekly.",
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


def _usr(eid: str, text: str, item: dict | None = None) -> dict:
    ev = {"event_id": eid, "kind": "user_message", "text": text}
    if item:
        ev["item"] = item
    return ev


def _upd(eid: str, item_id: str, item: dict, text: str) -> dict:
    return {"event_id": eid, "kind": "memory_update", "text": text, "item_id": item_id, "item": item}


def _fgt(eid: str, item_id: str, text: str) -> dict:
    return {"event_id": eid, "kind": "memory_forget", "text": text, "item_id": item_id}


def _qry(eid: str, text: str) -> dict:
    return {"event_id": eid, "kind": "query", "text": text}


def _emit(
    row: dict,
    events: list[dict],
    query: str,
    gt_required: list[str],
    gt_forbidden: list[str],
    expected_op: str,
    memory_trace: list[str],
    required_item_ids: list[str],
    tags: list[str],
) -> dict:
    distractor_ids = [e["event_id"] for e in events if e["kind"] == "user_message" and "item" not in e]
    task = {
        "task_id": row["task_id"],
        "benchmark_version": "v0.1",
        "category": row["category"],
        "difficulty": row["difficulty"],
        "description": row["brief"],
        "scenario": SCENARIO,
        "tags": sorted(set(tags + [row["template"]])),
        "events": events,
        "query": query,
        "distractor_event_ids": distractor_ids,
        "ground_truth": {"required_values": list(gt_required), "forbidden_values": list(gt_forbidden)},
        "success_criterion": {
            "type": "contains_all",
            "values": [v.lower() for v in gt_required],
            "forbid": [v.lower() for v in gt_forbidden],
            "normalization": "lower_strip",
        },
        "expected_memory_operation": expected_op,
        "memory_trace": list(memory_trace),
        "required_item_ids": list(required_item_ids),
        "failure_categories": row.get("failure_categories") or _default_failure_cats(row["category"]),
        "seed": row["seed"],
    }
    errors = validate_task(task)
    if errors:
        raise RuntimeError(f"generated invalid task {row['task_id']}: {'; '.join(errors)}")
    return task


def _default_failure_cats(category: str) -> list[str]:
    base = ["RETRIEVAL_FAILURE", "IRRELEVANT_MEMORY_INTERFERENCE", "REASONING_FAILURE"]
    if category == "retention":
        return ["RETENTION_FAILURE"] + base
    if category == "updating":
        return ["UPDATE_FAILURE"] + base
    if category == "stale_conflict":
        return ["STALE_MEMORY_FAILURE"] + base
    if category == "forgetting":
        return ["FORGETTING_FAILURE", "REASONING_FAILURE"]
    if category == "adversarial":
        return ["ADVERSARIAL_MEMORY_FAILURE"] + base
    raise ValueError(category)


# ---------------------------------------------------------------------------
# Frozen entity pools (each variant: label, value, mention sentence, ask sentence)
# ---------------------------------------------------------------------------

_TEAMS = [
    ("Office trivia team name", "The Ferric Falcons", "By the way, our office trivia team is called the Ferric Falcons.", "What is the name of our office trivia team?"),
    ("Company bowling team name", "Nightwatch Coders", "Heads up: our bowling team is called Nightwatch Coders.", "What is the company bowling team called?"),
    ("Hackathon team name", "Meme Oracles", "We registered 'Meme Oracles' for the hackathon.", "What team did we register for the hackathon?"),
    ("Charity run team name", "Sable Striders", "Our charity run team is the Sable Striders.", "What is our charity run team called?"),
]

_IDS = [
    ("West wing table numbering scheme", "TR-ALP-14", "We're using TR-ALP-14 for the west wing tables.", "Which numbering scheme are the west wing tables using?"),
    ("Ferric Labs stock order code", "OR-7729-K", "Our stock order code is OR-7729-K.", "What is our stock order code?"),
    ("Vendor account handle", "vendor_7a2f", "The vendor account handle is vendor_7a2f.", "What is the vendor account handle?"),
    ("Document archive key", "DR-2026-QUA", "The archive key is DR-2026-QUA.", "What archive key are we using?"),
]

_ROOMS = [
    ("Planning sync location", "Room Verve", "The planning sync is in Room Verve tomorrow.", "Where is the planning sync being held tomorrow?"),
    ("Team lunch spot", "Cafe Moorline", "Team lunch is booked at Cafe Moorline.", "Where is team lunch booked?"),
    ("Client visit room", "Room Sable", "The client visit is in Room Sable.", "Which room is the client visit in?"),
]

_MILESTONES = [
    ("Release date for the Quilldash app v2.0", "December 1st", "The Quilldash v2.0 release date is confirmed as December 1st.", "When is Quilldash v2.0 being released?"),
    ("Launch date for the Ledgerfly beta", "March 14th", "Ledgerfly beta launches on March 14th.", "When does Ledgerfly beta launch?"),
    ("Signetly redesign go-live date", "June 22nd", "The Signetly redesign goes live June 22nd.", "When does the Signetly redesign go live?"),
]

_PREFS = [
    ("User drink preference", "oolong tea", "For the record, I prefer oolong tea.", "What should I order at the cafe given my drink preference?"),
    ("User seat assignment", "Desk 14B", "I've been assigned Desk 14B.", "What seat am I assigned to?"),
    ("User login language", "Finnish", "I switched my login language to Finnish.", "What login language do I use?"),
]

_DECOY_PREFS = [
    "And for snacks, I'd rather have the salted shortbread.",
    "For lunch breaks I usually take the Mediterranean bowl.",
    "I always book the standing desk by the window.",
]

_VALUES = _TEAMS + _IDS + _ROOMS + _MILESTONES + _PREFS

# update / stale / adversarial variants
_UPD_PAIRS = [
    ("User drink preference", "macchiato", "Matcha Keep", "I prefer macchiato.", "Actually, I've switched to Matcha Keep.", "What should I order at the cafe given my drink preference?"),
    ("Planning sync location", "Room Sable", "Room Verve", "The planning sync is in Room Sable.", "We moved the planning sync to Room Verve.", "Where is the planning sync being held now?"),
    ("Team lunch spot", "Cafe Limeprint", "Cafe Moorline", "Team lunch is at Cafe Limeprint.", "Switch team lunch to Cafe Moorline.", "Where is team lunch booked?"),
    ("West wing table scheme", "TR-ALP-14", "TR-BRA-02", "The west wing uses TR-ALP-14.", "Change the west wing tables to TR-BRA-02.", "Which numbering scheme are the west wing tables using?"),
    ("Release date for Quilldash v2.1", "October 5th", "October 19th", "Quilldash v2.1 ships October 5th.", "Slide Quilldash v2.1 to October 19th.", "When does Quilldash v2.1 ship?"),
    ("Demo account security answer", "Callisto", "Europa", "The demo security answer is Callisto.", "Set the demo security answer to Europa.", "What is the demo security answer?"),
]

_STALE_PAIRS = [
    ("Planning sync location", "Room Sable", "Room Verve",
     "The planning sync is in Room Sable tomorrow.", "Heads up, we're moving the planning sync to Room Verve.",
     "Where is the planning sync being held now?"),
    ("Hackathon venue", "The Foundry Space", "Gridworks Hall",
     "The hackathon is at The Foundry Space.", "Some people said the hackathon moved to Gridworks Hall.",
     "Where is the hackathon being held?"),
    ("Lunch delivery window", "12:30", "13:00",
     "Lunch delivery window is 12:30.", "The runner mentioned the window is now 13:00.",
     "What is the lunch delivery window?"),
    ("Marketing page owner", "Priya", "Marco",
     "Priya owns the marketing page.", "Word around the office is the page owner is Marco now.",
     "Who owns the marketing page?"),
]

_ADS_PAIRS = [
    ("Release date for the Quilldash app v2.0", "December 1st", "March 1st",
     "The Quilldash v2.0 release date is confirmed as December 1st.",
     "Someone in the office chat claims the release is March 1st and the December date was a rumor.",
     "Quilldash's office pool",
     "When is Quilldash v2.0 being released?"),
    ("Parking assignment for the new garage", "Garage B", "Garage A",
     "Your parking assignment is Garage B.",
     "A random post says your parking is actually Garage A.",
     "anonymous comment thread",
     "Which garage are you assigned to?"),
    ("App store status for Ledgerfly", "Under review", "Published",
     "Ledgerfly is under review in the app store.",
     "A stranger in the community forum says it's already published.",
     "forum account 'appguru99'",
     "What is the app store status for Ledgerfly?"),
]

# ---------------------------------------------------------------------------
# Template implementations
# ---------------------------------------------------------------------------


def _distractors(rng: random.Random, n: int, used: set[str]) -> list[str]:
    pool = [d for d in DISTRACTORS if d not in used]
    chosen = rng.sample(pool, k=n)
    used.update(chosen)
    return chosen


def _retention(row: dict, pick: tuple, distractor_count: int, similar: bool = False,
               combine: tuple | None = None, decoy: bool = False) -> dict:
    rng = random.Random(row["seed"])
    used: set[str] = set()
    label, value, mention, ask = pick
    events = [_usr("e1", mention, item=_item("m1", f"{label}: {value}.", "user", 1, 1.0, False, "user"))]
    trace = ["ADD m1"]
    required = ["m1"]
    gt_required = [value]
    gt_forbidden: list[str] = []
    tags = ["single_fact"]
    eid = 2
    if decoy:
        _label2, _value2, mention2, _ask2 = rng_pick(row, _VALUES)
        events.append(_usr(f"e{eid}", mention2, item=_item("m2", f"{_label2}: {_value2}.", "user", eid, 1.0, False, "user")))
        trace.append("ADD m2")
        tags.append("decoy")
        eid += 1
    distractors = _distractors(rng, distractor_count, used)
    for d in distractors:
        events.append(_usr(f"e{eid}", d))
        eid += 1
    if similar:
        events.append(_usr(f"e{eid}", rng.choice(_DECOY_PREFS)))
        eid += 1
        tags.append("similar_distractor")
    if combine:
        label2, value2, mention2, ask2 = combine
        events.append(_usr(f"e{eid}", mention2, item=_item("m2", f"{label2}: {value2}.", "user", eid, 1.0, False, "user")))
        trace.append("ADD m2")
        required.append("m2")
        gt_required.append(value2)
        tags.append("multi_fact")
        ask = f"What is the {label.lower()} and what is the {label2.lower()}?"
        eid += 1
        for d in _distractors(rng, 1, used):
            events.append(_usr(f"e{eid}", d))
            eid += 1
    events.append(_qry(f"e{eid}", ask))
    return _emit(
        row, events, ask, gt_required, gt_forbidden,
        expected_op="memory_add of the earlier item(s); answer reproduces it (them) at query.",
        memory_trace=trace, required_item_ids=required, tags=tags,
    )


_CHAINED_PAIRS = [
    ("User drink preference", "macchiato", "black tea", "Matcha Keep",
     "For the record, I prefer macchiato.", "Make it black tea instead.", "Actually, make it Matcha Keep — final answer.",
     "What should I order at the cafe given my drink preference?"),
    ("Planning sync location", "Room Sable", "Room Verve", "The Wren Annex",
     "The planning sync is in Room Sable.", "Move it to Room Verve.", "Scratch that — the Wren Annex.",
     "Where is the planning sync being held now?"),
    ("Team lunch spot", "Cafe Limeprint", "Brew & Staple", "Cafe Moorline",
     "Team lunch is at Cafe Limeprint.", "Book Brew & Staple instead.", "No, final: Cafe Moorline.",
     "Where is team lunch booked?"),
]


def _update(row: dict, pick: tuple, distractors_before: int, distractors_after: int) -> dict:
    rng = random.Random(row["seed"])
    used: set[str] = set()
    label, old, new, mention_old, mention_new, ask = pick
    events = [_usr("e1", mention_old, item=_item("m1", f"{label}: {old}.", "user", 1, 1.0, False, "user"))]
    trace = ["ADD m1"]
    eid = 2
    for d in _distractors(rng, distractors_before, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    ts = eid
    events.append(_upd(f"e{eid}", "m1", _item("m1", f"{label}: {new}.", "user", ts, 1.0, False, "user"), mention_new))
    trace.append("UPDATE m1")
    eid += 1
    for d in _distractors(rng, distractors_after, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    events.append(_qry(f"e{eid}", ask))
    return _emit(
        row, events, ask, [new], [old],
        expected_op="memory.add(m1 old); authoritative memory.update(m1 -> new); answer follows the new value.",
        memory_trace=trace, required_item_ids=["m1"],
        tags=["authoritative_update", "single_update"],
    )


def _update_chained(row: dict, pick: tuple, distractors_after: int) -> dict:
    rng = random.Random(row["seed"])
    used: set[str] = set()
    label, old, mid, new, mention_old, mention_mid, mention_new, ask = pick
    events = [_usr("e1", mention_old, item=_item("m1", f"{label}: {old}.", "user", 1, 1.0, False, "user"))]
    trace = ["ADD m1"]
    events.append(_upd("e2", "m1", _item("m1", f"{label}: {mid}.", "user", 2, 1.0, False, "user"), mention_mid))
    trace.append("UPDATE m1")
    events.append(_upd("e3", "m1", _item("m1", f"{label}: {new}.", "user", 3, 1.0, False, "user"), mention_new))
    trace.append("UPDATE m1")
    eid = 4
    for d in _distractors(rng, distractors_after, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    events.append(_qry(f"e{eid}", ask))
    return _emit(
        row, events, ask, [new], [old, mid],
        expected_op="two chained authoritative updates; the final value governs.",
        memory_trace=trace, required_item_ids=["m1"],
        tags=["authoritative_update", "chained"],
    )


def _stale(row: dict, pick: tuple, distractors: int, mode: str = "recency") -> dict:
    rng = random.Random(row["seed"])
    used: set[str] = set()
    label, old, new, mention_old, mention_new, ask = pick
    events = [_usr("e1", mention_old, item=_item("m1", f"{label}: {old}.", "team_lead", 1, 0.9, False, "team"))]
    trace = ["ADD m1"]
    eid = 2
    source = "team_lead"
    conf = 0.9 if mode != "low_conf" else 0.4
    authority = "team" if mode != "low_conf" else "junior"
    for d in _distractors(rng, distractors, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    events.append(_usr(f"e{eid}", mention_new, item=_item("m2", f"{label}: {new}.", source, eid, conf, False, authority)))
    trace.append("ADD m2")
    eid += 1
    for d in _distractors(rng, 1, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    events.append(_qry(f"e{eid}", ask))
    return _emit(
        row, events, ask, [new], [old],
        expected_op="conflicting adds (no directive); the system must resolve toward the more recent/authoritative value.",
        memory_trace=trace, required_item_ids=["m2"],
        tags=[f"stale_{mode}"],
    )


def _forget(row: dict, value: str, label: str, mention: str, ask: str,
            distractors_after: int, oblique: bool = False, keep_item: tuple | None = None) -> dict:
    rng = random.Random(row["seed"])
    used: set[str] = set()
    events = [_usr("e1", mention, item=_item("m1", f"{label}: {value}.", "user", 1, 1.0, False, "user"))]
    trace = ["ADD m1"]
    eid = 2
    events.append(_fgt(f"e{eid}", "m1", f"We're retiring that record; please forget the {label.lower()}."))
    trace.append("FORGET m1")
    eid += 1
    gt_required: list[str] = []
    gt_forbidden = [value]
    tags = ["explicit_forget"]
    final_query = ask
    if keep_item:
        kl, kv, km, ka = keep_item
        for d in _distractors(rng, 1, used):
            events.append(_usr(f"e{eid}", d))
            eid += 1
        events.append(_usr(f"e{eid}", km, item=_item("m2", f"{kl}: {kv}.", "user", eid, 1.0, False, "user")))
        trace.append("ADD m2")
        eid += 1
        final_query = ka
        gt_required = [kv]
        tags.append("also_retain")
    for d in _distractors(rng, distractors_after, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    if oblique:
        final_query = "Without re-reading specifics, what is the current status of that record?"
    events.append(_qry(f"e{eid}", final_query))
    return _emit(
        row, events, final_query, gt_required, gt_forbidden,
        expected_op="memory.add(m1); memory.forget(m1); the value must not resurface or be used at query.",
        memory_trace=trace, required_item_ids=["m2"] if keep_item else [],
        tags=tags,
    )


def _adversarial(row: dict, pick: tuple, distractors: int, poisoned_conf: float, similar: bool = False,
                 multi: bool = False, embedded_helpful: bool = False) -> dict:
    rng = random.Random(row["seed"])
    used: set[str] = set()
    label, trusted, poisoned, mention_trusted, mention_poisoned, src, ask = pick
    events = [_usr("e1", mention_trusted, item=_item("m1", f"{label}: {trusted}.", "product_manager" if "release" in label else "admin", 1, 1.0, False, "high"))]
    trace = ["ADD m1"]
    eid = 2
    for d in _distractors(rng, distractors, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    poisoned_value = poisoned
    if embedded_helpful:
        events.append(_usr(f"e{eid}", "For reference, the catering menu is final and the parking passes are printed.",
                          item=_item("m3", f"Catering menu status: final.", "office_ops", eid, 0.9, False, "team")))
        trace.append("ADD m3")
        eid += 1
    poison_conf = poisoned_conf
    events.append(_usr(f"e{eid}", mention_poisoned,
                       item=_item("m2", f"{label}: {poisoned_value}.", src, eid, poison_conf, True, "untrusted")))
    trace.append("ADD m2")
    eid += 1
    forbid = [poisoned_value]
    if multi:
        extra = "May 21st" if poisoned_value != "May 21st" else "February 8th"
        events.append(_usr(f"e{eid}", f"Also, someone else insists it is {extra}.",
                           item=_item("m3", f"{label}: {extra}.", "second_anonymous", eid, 0.15, True, "untrusted")))
        trace.append("ADD m3")
        forbid.append(extra)
        eid += 1
    for d in _distractors(rng, 1, used):
        events.append(_usr(f"e{eid}", d))
        eid += 1
    events.append(_qry(f"e{eid}", ask))
    return _emit(
        row, events, ask, [trusted], forbid,
        expected_op="trusted m1 and untrusted m2 (adversarial flag, hidden from the model) both stored; answer must follow the trusted value.",
        memory_trace=trace, required_item_ids=["m1"],
        tags=["poisoning", "similar_poison" if similar else "poisoning", "multi_poison" if multi else "poisoning", "embedded_helpful" if embedded_helpful else "poisoning"],
    )


def rng2(ctx, pool):
    return [p for p in pool if p][0]


# ---------------------------------------------------------------------------
# Dispatch: manifest template -> builder
# ---------------------------------------------------------------------------

def _b_ret_single_id(row): return _retention(row, rng_pick(row, _IDS), 1)
def _b_ret_name_1dist(row): return _retention(row, rng_pick(row, _TEAMS), 1)
def _b_ret_date_1dist(row): return _retention(row, rng_pick(row, _MILESTONES), 1)
def _b_ret_id_3dist(row): return _retention(row, rng_pick(row, _IDS), 3)
def _b_ret_pref_simdist(row): return _retention(row, rng_pick(row, _PREFS), 2, similar=True)
def _b_ret_fact_ignore_decoy(row): return _retention(row, rng_pick(row, _VALUES), 1, decoy=True)
def _b_ret_combine_2(row): return _retention(row, rng_pick(row, _TEAMS), 5, combine=rng_pick(row, _IDS))
def _b_ret_combine_simdist(row): return _retention(row, rng_pick(row, _PREFS), 4, similar=True, combine=rng_pick(row, _IDS))


def rng_pick(row: dict, pool: list) -> tuple:
    return pool[row["seed"] % len(pool)]


def _b_upd_immediate(row): return _update(row, rng_pick(row, _UPD_PAIRS), 0, 0)
def _b_upd_1dist(row): return _update(row, rng_pick(row, _UPD_PAIRS), 0, 1)
def _b_upd_location_1dist(row): return _update(row, rng_pick(row, _UPD_PAIRS), 1, 0)
def _b_upd_3dist(row): return _update(row, rng_pick(row, _UPD_PAIRS), 0, 3)
def _b_upd_double(row): return _update_chained(row, rng_pick(row, _CHAINED_PAIRS), 2)
def _b_upd_one_of_two(row): return _update(row, rng_pick(row, _UPD_PAIRS), 1, 1)


def _b_upd_5dist_after_update(row): return _update(row, rng_pick(row, _UPD_PAIRS), 0, 5)
def _b_upd_chained(row): return _update_chained(row, rng_pick(row, _CHAINED_PAIRS), 3)


def _b_stl_immediate_conflict(row): return _stale(row, rng_pick(row, _STALE_PAIRS), 1)
def _b_stl_recent_wins(row): return _stale(row, rng_pick(row, _STALE_PAIRS), 0)
def _b_stl_authority_wins(row): return _stale(row, rng_pick(row, _STALE_PAIRS), 0, mode="authority")
def _b_stl_3dist(row): return _stale(row, rng_pick(row, _STALE_PAIRS), 3)


def _b_stl_old_similar(row):
    rng = random.Random(row["seed"])
    pick = _STALE_PAIRS[rng.randrange(len(_STALE_PAIRS))]
    # Semantic closeness of the old value is already embedded via same-label conflicts.
    return _stale(row, pick, 2)


def _b_stl_three_values_middle(row):
    rng = random.Random(row["seed"])
    label, old, new, m1, m2, ask = _STALE_PAIRS[rng.randrange(len(_STALE_PAIRS))]
    bogus = rng.choice([v for pair in _STALE_PAIRS for v in pair[1:3] if v not in (old, new)] + ["The Gable Loft"])
    events = [
        _usr("e1", m1, item=_item("m1", f"{label}: {old}.", "team_lead", 1, 0.9, False, "team")),
        _usr("e2", m2, item=_item("m2", f"{label}: {new}.", "team_lead", 2, 0.9, False, "team")),
        _usr("e3", f"Something about concatenating again surfaced, saying it is now {bogus}.",
             item=_item("m3", f"{label}: {bogus}.", "office_ops", 3, 0.8, False, "junior")),
    ]
    trace = ["ADD m1", "ADD m2", "ADD m3"]
    events.append(_qry("e4", ask))
    return _emit(
        row, events, ask, [new], [old, bogus],
        expected_op="three conflicting adds; correct value is the middle one (m2); the system must not follow either extreme.",
        memory_trace=trace, required_item_ids=["m2"],
        tags=["three_way_conflict"],
    )


def _b_stl_5dist(row): return _stale(row, rng_pick(row, _STALE_PAIRS), 5)


def _b_stl_confirmed_low_conf(row):
    rng = random.Random(row["seed"])
    pick = _STALE_PAIRS[rng.randrange(len(_STALE_PAIRS))]
    return _stale(row, pick, 2, mode="low_conf")


def _b_fgt_immediate(row):
    v = rng_pick(row, _UPD_PAIRS)
    return _forget(row, v[1], v[0], f"Set aside: {v[0].lower()} is {v[1]}.", v[5], 0)


def _b_fgt_1dist(row):
    v = rng_pick(row, _UPD_PAIRS)
    return _forget(row, v[1], v[0], f"For the books: {v[0].lower()} is {v[1]}.", v[5], 1)


def _b_fgt_number(row):
    label, value, mention, ask = rng_pick(row, _IDS)
    return _forget(row, value, label, f"Noted for billing: {label.lower()} is {value}.", "What is the unprocessed billing detail?", 1)


def _b_fgt_3dist(row):
    v = rng_pick(row, _UPD_PAIRS)
    return _forget(row, v[1], v[0], f"Just so we have it: {v[0].lower()} is {v[1]}.", v[5], 3)


def _b_fgt_circleback(row):
    v = rng_pick(row, _UPD_PAIRS)
    task = _forget(row, v[1], v[0], f"Keep this handy: {v[0].lower()} is {v[1]}.", v[5], 2)
    # insert a circle-back comment before the query (re-topic mention, no stored item)
    events = task["events"]
    qry = events[-1]
    eid = f"e{len(events) + 1}"
    events.insert(-1, _usr(eid, f"Oh, and the others were asking about the {v[0].lower()} again."))
    events[-1] = qry
    task["events"] = events
    return task


def _b_fgt_one_of_two(row):
    v = rng_pick(row, _UPD_PAIRS)
    keep = rng_pick(row, _IDS)
    return _forget(row, v[1], v[0], f"Write it down: {v[0].lower()} is {v[1]}.", v[5], 1, keep_item=keep)


def _b_fgt_oblique(row):
    v = rng_pick(row, _UPD_PAIRS)
    return _forget(row, v[1], v[0], f"Note it: {v[0].lower()} is {v[1]}.", "What is the current status of that record?", 2, oblique=True)


def _b_fgt_similar_retained(row):
    v = rng_pick(row, _UPD_PAIRS)
    # retained item intentionally similar-labelled
    keep = (f"{v[0]} (backup)", "Vault Key 9", f"The backup {v[0].lower()} is Vault Key 9.", "What is the backup record?")
    return _forget(row, v[1], v[0], f"Remember: {v[0].lower()} is {v[1]}.", v[5], 1, keep_item=keep)


def _b_ads_immediate(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 0, 0.2)
def _b_ads_anon_source(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 1, 0.2)
_ADS_SIMILAR = [
    ("Release date for the Quilldash app v2.0", "December 1st", "December 10th",
     "The Quilldash v2.0 release date is confirmed as December 1st.",
     "Someone in the office chat claims the release is actually December 10th.",
     "secret_liaison",
     "When is Quilldash v2.0 being released?"),
]


def _b_ads_similar_poison(row): return _adversarial(row, rng_pick(row, _ADS_SIMILAR), 1, 0.2)
def _b_ads_late_poison(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 4, 0.2)
def _b_ads_conf_paradox(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 1, 0.9)
def _b_ads_multi_poison(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 2, 0.2, multi=True)
def _b_ads_both_values_5dist(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 5, 0.2, multi=True)
def _b_ads_embedded_helpful(row): return _adversarial(row, rng_pick(row, _ADS_PAIRS), 2, 0.2, embedded_helpful=True)


TEMPLATES: dict[str, Callable[[dict], dict]] = {
    "RET_SINGLE_ID": _b_ret_single_id,
    "RET_NAME_1DIST": _b_ret_name_1dist,
    "RET_DATE_1DIST": _b_ret_date_1dist,
    "RET_ID_3DIST": _b_ret_id_3dist,
    "RET_PREF_SIMDIST": _b_ret_pref_simdist,
    "RET_FACT_IGNORE_DECOY": _b_ret_fact_ignore_decoy,
    "RET_COMBINE_2": _b_ret_combine_2,
    "RET_COMBINE_SIMDIST": _b_ret_combine_simdist,
    "UPD_IMMEDIATE": _b_upd_immediate,
    "UPD_1DIST": _b_upd_1dist,
    "UPD_LOCATION_1DIST": _b_upd_location_1dist,
    "UPD_3DIST": _b_upd_3dist,
    "UPD_DOUBLE": _b_upd_double,
    "UPD_ONE_OF_TWO": _b_upd_one_of_two,
    "UPD_5DIST_AFTER_UPDATE": _b_upd_5dist_after_update,
    "UPD_CHAINED": _b_upd_chained,
    "STL_IMMEDIATE_CONFLICT": _b_stl_immediate_conflict,
    "STL_RECENT_WINS": _b_stl_recent_wins,
    "STL_AUTHORITY_WINS": _b_stl_authority_wins,
    "STL_3DIST": _b_stl_3dist,
    "STL_OLD_SIMILAR": _b_stl_old_similar,
    "STL_THREE_VALUES_MIDDLE": _b_stl_three_values_middle,
    "STL_5DIST": _b_stl_5dist,
    "STL_CONFIRMED_LOW_CONF": _b_stl_confirmed_low_conf,
    "FGT_IMMEDIATE": _b_fgt_immediate,
    "FGT_1DIST": _b_fgt_1dist,
    "FGT_NUMBER": _b_fgt_number,
    "FGT_3DIST": _b_fgt_3dist,
    "FGT_CIRCLEBACK": _b_fgt_circleback,
    "FGT_ONE_OF_TWO": _b_fgt_one_of_two,
    "FGT_OBLIQUE": _b_fgt_oblique,
    "FGT_SIMILAR_RETAINED": _b_fgt_similar_retained,
    "ADS_IMMEDIATE": _b_ads_immediate,
    "ADS_ANON_SOURCE": _b_ads_anon_source,
    "ADS_SIMILAR_POISON": _b_ads_similar_poison,
    "ADS_LATE_POISON": _b_ads_late_poison,
    "ADS_CONF_PARADOX": _b_ads_conf_paradox,
    "ADS_MULTI_POISON": _b_ads_multi_poison,
    "ADS_BOTH_VALUES_5DIST": _b_ads_both_values_5dist,
    "ADS_EMBEDDED_HELPFUL": _b_ads_embedded_helpful,
}


def generate_task(row: dict) -> dict:
    builder = TEMPLATES.get(row["template"])
    if builder is None:
        raise KeyError(f"unknown template: {row['template']}")
    return builder(row)


# alias used by helpers above (kept simple)
def rng2(ctx, pool):
    return [p for p in pool if p][0]


def generate_all(rows: list[dict]) -> list[dict]:
    tasks = [generate_task(r) for r in rows]
    ids = [t["task_id"] for t in tasks]
    if len(ids) != len(set(ids)):
        raise RuntimeError("duplicate task ids generated")
    return tasks