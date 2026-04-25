"""
Kafiya dictionary: given an Urdu word, return rhyming words grouped by
match quality (exact / close / open), with phonetic matches flagged.
"""

from __future__ import annotations

import json
import logging
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

    __slots__ = (
        "word",
        "match_kind",
        "meaning",
        "frequency_rank",
        "is_compound",
        "same_letter_count",
    )

    def __init__(
        self,
        word: str,
        match_kind: MatchKind,
        *,
        meaning: Optional[str] = None,
        frequency_rank: Optional[int] = None,
        is_compound: bool = False,
        same_letter_count: bool = False,
    ) -> None:
        self.word = word
        self.match_kind = match_kind
        self.meaning = meaning
        self.frequency_rank = frequency_rank
        self.is_compound = is_compound
        self.same_letter_count = same_letter_count

    def __repr__(self) -> str:
        return f"KafiyaMatch({self.word!r}, {self.match_kind!r})"

    def to_dict(self) -> Dict:
        out = {
            "word": self.word,
            "match_kind": self.match_kind,
            "is_compound": self.is_compound,
            "same_letter_count": self.same_letter_count,
        }
        if self.meaning:
            out["meaning"] = self.meaning
        if self.frequency_rank is not None:
            out["frequency_rank"] = self.frequency_rank
        return out


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
        word_metadata: Optional[dict[str, dict[str, object | None]]] = None,
        max_per_bucket: Optional[int] = 50,
    ) -> None:
        self._index = index
        self._word_metadata = word_metadata or {}
        self.max_per_bucket = max_per_bucket

    @classmethod
    def load(
        cls,
        pickle_path: str | Path,
        *,
        metadata_path: str | Path | None = None,
        max_per_bucket: Optional[int] = 50,
    ) -> "KafiyaDict":
        """Load a pre-built index from a pickle file."""
        with open(pickle_path, "rb") as fh:
            index = pickle.load(fh)
        word_metadata = cls._load_word_metadata(metadata_path)
        return cls(
            index,
            word_metadata=word_metadata,
            max_per_bucket=max_per_bucket,
        )

    @staticmethod
    def _load_word_metadata(
        metadata_path: str | Path | None,
    ) -> Optional[dict[str, dict[str, object | None]]]:
        """Load optional word metadata used to enrich dictionary results."""
        if metadata_path is None:
            return None

        try:
            with open(metadata_path, encoding="utf-8") as fh:
                loaded = json.load(fh)
        except FileNotFoundError:
            return None
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to load word metadata from %s", metadata_path
            )
            return None

        if not isinstance(loaded, dict):
            logging.getLogger(__name__).warning(
                "Ignoring word metadata from %s because the top-level JSON value is not an object",
                metadata_path,
            )
            return None

        return loaded

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

        query_letter_count = len(script_query)
        self._enrich_matches(exact_matches, query_letter_count)
        self._enrich_matches(close_matches, query_letter_count)
        self._enrich_matches(open_matches, query_letter_count)

        self._sort_matches(exact_matches)
        self._sort_matches(close_matches)
        self._sort_matches(open_matches)

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

    def _enrich_matches(
        self,
        matches: List[KafiyaMatch],
        query_letter_count: int,
    ) -> None:
        """Attach metadata and ranking features used by the dictionary UI."""
        for match in matches:
            match.is_compound = "_" in match.word or " " in match.word
            lookup_word = match.word.replace("_", " ")
            normalized_lookup_word = normalize_urdu_text(lookup_word)
            match.same_letter_count = len(normalized_lookup_word) == query_letter_count

            if not self._word_metadata:
                continue

            entry = self._word_metadata.get(normalized_lookup_word)
            if not isinstance(entry, dict):
                continue
            meaning = entry.get("meaning")
            if isinstance(meaning, str) and meaning:
                match.meaning = meaning
            frequency_rank = entry.get("frequency_rank")
            if isinstance(frequency_rank, int):
                match.frequency_rank = frequency_rank

    def _sort_matches(self, matches: List[KafiyaMatch]) -> None:
        """Sort candidates by poetic usefulness for dictionary browsing."""
        matches.sort(
            key=lambda match: (
                match.is_compound,
                not match.same_letter_count,
                0 if match.match_kind == "script" else 1,
                match.frequency_rank is None,
                match.frequency_rank if match.frequency_rank is not None else 0,
                not bool(match.meaning),
                match.word,
            )
        )

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
