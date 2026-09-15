from src.memory.base import MemoryItem, MemoryLogger
from src.memory.naive_retrieval import NaiveRetrieval
from src.memory.no_memory import NoMemory
from src.memory.sacam_v0 import SACAMv0
from src.memory.sacam_v1 import SACAMv1
from src.memory.structured_memory import StructuredMemory


def _item(iid, content, ts=1, source="team_lead", conf=0.9, forbidden=False, authority="team"):
    return MemoryItem(iid, f"{content}.", {"timestamp": ts, "source": source, "confidence": conf,
                                            "is_poisoned": forbidden, "authority": authority})


def test_no_memory_never_retains():
    m = NoMemory(0, MemoryLogger())
    m.add(_item("m1", "Kestrel Prime is Scorch"))
    assert m.inspect() == []
    assert m.retrieve("Kestrel Prime", 3) == []


def test_naive_basic_roundtrip():
    m = NaiveRetrieval(0, MemoryLogger())
    m.add(_item("m1", "Kestrel Prime is Scorch", ts=1))
    m.add(_item("m2", "Vault key is Cascade-77", ts=2))
    hits = [(r.item_id, round(r.score, 6)) for r in m.retrieve("Kestrel Prime", 3)]
    assert hits[0][0] == "m1"


def test_structure_newest_wins():
    m = StructuredMemory(0, MemoryLogger())
    m.add(_item("m1", "Lead mentor is Iris Vale", ts=1))
    m.update("m1", _item("m1", "Lead mentor is Otis Kane", ts=2))
    store = m.inspect()
    assert len(store) == 1
    assert store[0].content == "Lead mentor is Otis Kane."
    hits = [r.item_id for r in m.retrieve("Lead mentor is", 3)]
    assert "m1" in hits


def test_forget_removes():
    m = StructuredMemory(0, MemoryLogger())
    m.add(_item("m1", "Vault key is Cascade-77", ts=1))
    m.add(_item("m2", "Billing code is PDQ-900", ts=2))
    m.forget("m1")
    assert [i.item_id for i in m.inspect()] == ["m2"]
    assert "m1" not in [r.item_id for r in m.retrieve("Vault key", 3)]


def test_sacam_v0_manages_superseded_and_untrusted():
    log = MemoryLogger()
    m = SACAMv0(0, log)
    m.add(_item("m1", "Release date is March 3rd", ts=1, source="trusted"))
    m.update("m1", _item("m1", "Release date is June 10th", ts=2, source="trusted"))
    m.add(_item("m2", "Release date is March 3rd", ts=3, source="jonas_network", conf=0.2, forbidden=True))
    retrieved = m.retrieve("Release date", 3)
    top = retrieved[0]
    assert top.item_id == "m1"
    ranking = [r.item_id for r in retrieved]
    assert ranking.index("m1") <= ranking.index("m2")


def test_sacam_v1_never_supersedes_stronger_claim():
    """v0.2 fix: an untrusted impostor must not bury a high-confidence trusted claim."""
    m = SACAMv1(0, MemoryLogger())
    m.add(_item("m1", "Release date: December 1st", ts=1, source="admin", conf=1.0))
    m.add(_item("m2", "Release date: March 1st", ts=2, source="office_pool", conf=0.2, forbidden=True))
    assert "m1" not in m._superseded, "trusted claim must not be marked superseded"
    retrieved = m.retrieve("Release date", 3)
    assert retrieved[0].item_id == "m1"
    assert m._multiplier(m._items["m1"]) > m._multiplier(m._items["m2"])


def test_sacam_v1_still_supersedes_stronger_new_claim():
    """A distinct, same-label, stronger new claim still supersedes the old one."""
    m = SACAMv1(0, MemoryLogger())
    m.add(_item("m1", "Release date: March 3rd", ts=1, source="junior", conf=0.7))
    m.add(_item("m2", "Release date: June 10th", ts=2, source="admin", conf=1.0))
    assert "m1" in m._superseded
    retrieved = m.retrieve("Release date", 3)
    assert retrieved[0].item_id == "m2"


def test_full_context_is_naive_with_all():
    m = NaiveRetrieval(0, MemoryLogger())
    for i in range(5):
        m.add(_item(f"m{i}", f"fact number {i}", ts=i))
    hits = m.retrieve("something unrelated", -1)
    assert len(hits) == 5


def test_memory_logger_tracks_ops():
    log = MemoryLogger()
    m = StructuredMemory(0, log)
    m.forget("mX")
    m.update("mY", _item("mY", "v", ts=1))
    assert "mX" in log.forget_target_ids()
    assert any(e["op"] == "update" for e in log.snapshot())