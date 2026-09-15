"""Deterministic term-overlap retrieval machinery (no RNG, no external APIs)."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter

# Frozen English stop-list. Changing this list changes retrieval behaviour and is
# therefore a protocol change (requires a new benchmark version).
STOPWORDS = frozenset(
    """
    a about above after again all also am an and any are as at be because been before
    being below between both but by can could did do does doing down during each few for
    from further had has have having he her here hers herself him himself his how i if in
    into is it its itself just me more most my myself no nor not now of off on once only
    or other our ours ourselves out over own same she should so some such than that the
    their theirs them themselves then there these they this those through to too under
    until up very was we were what when where which while who whom why will with you your
    yours yourself yourselves
    """.split()
)


def normalize_text(text: str) -> str:
    """Lowercase, fold unicode, split into tokens on non-alphanumerics."""
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return " ".join(t for t in tokens if t not in STOPWORDS and len(t) > 1)


def token_counts(text: str) -> Counter:
    return Counter(normalize_text(text).split())


class TermIndex:
    """Deterministic bag-of-words index with IDF weighting.

    Scores an item by the sum of inverse-document-frequencies of query tokens that
    the item contains (TF capped at 1 for simplicity). Ties broken by item_id so the
    whole procedure is a pure function of (store, query, stoplist).
    """

    def __init__(self, docs: dict[str, str]):
        """docs: {item_id: text_for_indexing}."""
        self._docs = {iid: token_counts(text) for iid, text in docs.items()}
        self._token_doc_freq: Counter = Counter()
        for counts in self._docs.values():
            for tok in counts:
                self._token_doc_freq[tok] += 1
        n = max(len(self._docs), 1)
        self._idf = {
            tok: math.log((n + 1.0) / (freq + 1.0)) + 1.0
            for tok, freq in self._token_doc_freq.items()
        }

    def score(self, query: str, item_id: str) -> float:
        q = token_counts(query)
        item = self._docs[item_id]
        score = 0.0
        for tok, qf in q.items():
            if tok in item:
                score += self._idf.get(tok, 1.0) * qf
        return score

    def rank(self, query: str, ids: list[str], decrease: dict[str, float] | None = None) -> list[tuple[str, float]]:
        """Return (item_id, score) sorted desc. Optional per-item multiplier."""

        scored = []
        for iid in ids:
            base = self.score(query, iid)
            mult = (decrease or {}).get(iid, 1.0)
            scored.append((mult * base, iid))
        scored.sort(key=lambda pair: (-pair[0], pair[1]))
        return [(iid, s) for s, iid in scored]