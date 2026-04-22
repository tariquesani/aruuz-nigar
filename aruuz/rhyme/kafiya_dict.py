"""
Kafiya dictionary: given an Urdu word, return rhyming words grouped by
match quality (exact / close / open), with phonetic matches flagged.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Literal, Optional

from aruuz.rhyme.text_utils import (
    full_normalize,
    is_urdu_vowel_letter,
    normalize_urdu_text,
)


MatchKind = Literal["script", "phonetic"]
OpenGuardClass = Literal["vowel", "semi_vowel", "non_vowel"]

SEMI_VOWEL_LETTERS = frozenset({"و", "ی", "ے"})


class KafiyaMatch:
    """A single rhyming word with provenance."""

    __slots__ = ("word", "match_kind")

    def __init__(self, word: str, match_kind: MatchKind) -> None:
        self.word = word
        self.match_kind = match_kind

    def __repr__(self) -> str:
        return f"KafiyaMatch({self.word!r}, {self.match_kind!r})"

    def to_dict(self) -> Dict:
        return {"word": self.word, "match_kind": self.match_kind}


class KafiyaResult:
    """
    Grouped lookup result returned by KafiyaDict.lookup().
    """

    def __init__(
        self,
        query: str,
        suffix_lengths: Dict[str, int],
        exact: List[KafiyaMatch],
        close: List[KafiyaMatch],
        open_: List[KafiyaMatch],
    ) -> None:
        self.query = query
        self.suffix_lengths = suffix_lengths
        self.exact = exact
        self.close = close
        self.open = open_

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "suffix_lengths": self.suffix_lengths,
            "exact": [m.to_dict() for m in self.exact],
            "close": [m.to_dict() for m in self.close],
            "open": [m.to_dict() for m in self.open],
        }

    def __repr__(self) -> str:
        return (
            f"KafiyaResult(query={self.query!r}, "
            f"exact={len(self.exact)}, "
            f"close={len(self.close)}, "
            f"open={len(self.open)})"
        )


class KafiyaDict:
    """Poet-facing kafiya lookup tool."""

    def __init__(
        self,
        index: dict,
        *,
        max_per_bucket: Optional[int] = 50,
    ) -> None:
        self._index = index
        self.max_per_bucket = max_per_bucket

    @classmethod
    def load(
        cls,
        pickle_path: str | Path,
        *,
        max_per_bucket: Optional[int] = 50,
    ) -> "KafiyaDict":
        """Load a pre-built index from a pickle file."""
        with open(pickle_path, "rb") as fh:
            index = pickle.load(fh)
        return cls(index, max_per_bucket=max_per_bucket)

    def lookup(
        self,
        query: str,
        *,
        max_per_bucket: Optional[int] = None,
    ) -> KafiyaResult:
        """
        Find kafiya matches for *query* grouped into three quality buckets.
        """
        limit = max_per_bucket if max_per_bucket is not None else self.max_per_bucket

        script_query = normalize_urdu_text(query)
        phonetic_query = full_normalize(query)

        max_possible = len(phonetic_query) - 1
        if max_possible < 1:
            return KafiyaResult(
                query=script_query,
                suffix_lengths={"exact": 0, "close": 0, "open": 0},
                exact=[],
                close=[],
                open_=[],
            )

        exact_len = 0
        for n in range(min(max_possible, 4), 2, -1):
            if self._index.get((n, phonetic_query[-n:])):
                exact_len = n
                break

        close_len = 2 if max_possible >= 2 else 0
        open_len = 1

        suffix_lengths = {
            "exact": exact_len,
            "close": close_len,
            "open": open_len,
        }

        seen: set[str] = {script_query}

        exact_matches = (
            self._fetch_bucket(phonetic_query, script_query, exact_len, seen)
            if exact_len > 0
            else []
        )
        seen.update(m.word for m in exact_matches)

        close_matches = (
            self._fetch_bucket(phonetic_query, script_query, close_len, seen)
            if close_len >= 2
            else []
        )
        seen.update(m.word for m in close_matches)

        open_matches = (
            self._fetch_bucket(phonetic_query, script_query, open_len, seen)
            if open_len > 0
            else []
        )

        if limit is not None:
            exact_matches = exact_matches[:limit]
            close_matches = close_matches[:limit]
            open_matches = open_matches[:limit]

        return KafiyaResult(
            query=script_query,
            suffix_lengths=suffix_lengths,
            exact=exact_matches,
            close=close_matches,
            open_=open_matches,
        )

    def _classify_open_guard_letter(self, ch: str) -> OpenGuardClass:
        """Classify a penultimate letter for 1-letter dictionary matching."""
        if ch in SEMI_VOWEL_LETTERS:
            return "semi_vowel"
        if is_urdu_vowel_letter(ch):
            return "vowel"
        return "non_vowel"

    def _passes_open_guard(self, query_word: str, candidate_word: str) -> bool:
        """
        Filter 1-letter suffix matches using the query word as the guard source.

        Semi-vowels such as و / ی / ے are allowed to match either side of the
        implicit-a non-vowel class, which keeps common Urdu rhyme spellings
        discoverable without opening the bucket completely.
        """
        if len(query_word) < 2 or len(candidate_word) < 2:
            return False

        query_class = self._classify_open_guard_letter(query_word[-2])
        candidate_class = self._classify_open_guard_letter(candidate_word[-2])

        compatible_classes = {
            "vowel": {"vowel", "semi_vowel"},
            "semi_vowel": {"vowel", "semi_vowel", "non_vowel"},
            "non_vowel": {"semi_vowel", "non_vowel"},
        }
        return candidate_class in compatible_classes[query_class]

    def _fetch_bucket(
        self,
        phonetic_query: str,
        script_query: str,
        suffix_len: int,
        exclude: set[str],
    ) -> List[KafiyaMatch]:
        if suffix_len <= 0:
            return []

        phonetic_suffix = phonetic_query[-suffix_len:]
        raw_words: set[str] = self._index.get((suffix_len, phonetic_suffix), set())

        script_suffix = (
            script_query[-suffix_len:] if len(script_query) >= suffix_len else ""
        )

        matches: List[KafiyaMatch] = []
        for word in sorted(raw_words):
            if word in exclude:
                continue
            if suffix_len == 1 and not self._passes_open_guard(script_query, word):
                continue
            word_script_suffix = word[-suffix_len:] if len(word) >= suffix_len else word
            kind: MatchKind = (
                "script" if word_script_suffix == script_suffix else "phonetic"
            )
            matches.append(KafiyaMatch(word=word, match_kind=kind))

        return matches

__all__ = [
    "KafiyaDict",
    "KafiyaMatch",
    "KafiyaResult",
]
