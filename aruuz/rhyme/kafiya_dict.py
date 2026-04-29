"""
Kafiya dictionary: given an Urdu word, return rhyming words grouped by
match quality (exact / close / open), with phonetic matches flagged.
"""

from __future__ import annotations

import json
import logging
import os
import pickle
import re
from pathlib import Path
from typing import Dict, List, Literal, Optional

from aruuz.models import Words
from aruuz.rhyme.text_utils import (
    full_normalize,
    is_urdu_vowel_letter,
    normalize_urdu_text,
)
from aruuz.scansion import Scansion


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
        "vazn_codes",
        "vazn_match",
        "roman",
        "roman_tail3",
        "roman_tail2",
        "roman_tail3_match",
        "roman_tail2_match",
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
        vazn_codes: Optional[List[str]] = None,
        vazn_match: bool = False,
        roman: Optional[str] = None,
        roman_tail3: Optional[str] = None,
        roman_tail2: Optional[str] = None,
        roman_tail3_match: bool = False,
        roman_tail2_match: bool = False,
    ) -> None:
        self.word = word
        self.match_kind = match_kind
        self.meaning = meaning
        self.frequency_rank = frequency_rank
        self.is_compound = is_compound
        self.same_letter_count = same_letter_count
        self.vazn_codes = vazn_codes or []
        self.vazn_match = vazn_match
        self.roman = roman
        self.roman_tail3 = roman_tail3
        self.roman_tail2 = roman_tail2
        self.roman_tail3_match = roman_tail3_match
        self.roman_tail2_match = roman_tail2_match

    def __repr__(self) -> str:
        return f"KafiyaMatch({self.word!r}, {self.match_kind!r})"

    def to_dict(self) -> Dict:
        out = {
            "word": self.word,
            "match_kind": self.match_kind,
            "is_compound": self.is_compound,
            "same_letter_count": self.same_letter_count,
            "vazn_match": self.vazn_match,
        }
        if self.vazn_codes:
            out["vazn_codes"] = self.vazn_codes
        if self.meaning:
            out["meaning"] = self.meaning
        if self.frequency_rank is not None:
            out["frequency_rank"] = self.frequency_rank
        if self.roman:
            out["roman"] = self.roman
        if self.roman_tail3:
            out["roman_tail3"] = self.roman_tail3
        if self.roman_tail2:
            out["roman_tail2"] = self.roman_tail2
        if self.roman_tail3_match:
            out["roman_tail3_match"] = self.roman_tail3_match
        if self.roman_tail2_match:
            out["roman_tail2_match"] = self.roman_tail2_match
        return out


class KafiyaResult:
    """
    Grouped lookup result returned by KafiyaDict.lookup().
    """

    def __init__(
        self,
        query: str,
        query_vazn_codes: List[str],
        suffix_lengths: Dict[str, int],
        total_counts: Dict[str, int],
        exact: List[KafiyaMatch],
        close: List[KafiyaMatch],
        open_: List[KafiyaMatch],
    ) -> None:
        self.query = query
        self.query_vazn_codes = query_vazn_codes
        self.suffix_lengths = suffix_lengths
        self.total_counts = total_counts
        self.exact = exact
        self.close = close
        self.open = open_

    def to_dict(self) -> Dict:
        return {
            "query": self.query,
            "query_vazn_codes": self.query_vazn_codes,
            "suffix_lengths": self.suffix_lengths,
            "total_counts": self.total_counts,
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
        word_vazn_metadata: Optional[dict[str, list[str]]] = None,
        max_per_bucket: Optional[int] = 50,
    ) -> None:
        self._index = index
        self._word_metadata = word_metadata or {}
        self._word_vazn_metadata = word_vazn_metadata or {}
        self._scanner = Scansion()
        self.max_per_bucket = max_per_bucket

    @classmethod
    def load(
        cls,
        pickle_path: str | Path,
        *,
        metadata_path: str | Path | None = None,
        vazn_metadata_path: str | Path | None = None,
        max_per_bucket: Optional[int] = 50,
    ) -> "KafiyaDict":
        """Load a pre-built index from a pickle file."""
        pickle_path = Path(pickle_path)
        with open(pickle_path, "rb") as fh:
            index = pickle.load(fh)
        word_metadata = cls._load_word_metadata(metadata_path)
        if vazn_metadata_path is None:
            vazn_metadata_path = cls._resolve_word_vazn_metadata_path(pickle_path)
        word_vazn_metadata = cls._load_word_vazn_metadata(vazn_metadata_path)
        return cls(
            index,
            word_metadata=word_metadata,
            word_vazn_metadata=word_vazn_metadata,
            max_per_bucket=max_per_bucket,
        )

    @staticmethod
    def _resolve_word_vazn_metadata_path(pickle_path: Path) -> Path:
        """
        Resolve word_vazn_metadata.json near the index path.

        Priority:
        1) WORD_VAZN_METADATA_PATH environment override
        2) sibling of index pickle
        3) repo-level aruuz/database fallback derived from index location
        """
        env_override = os.getenv("WORD_VAZN_METADATA_PATH", "").strip()
        if env_override:
            return Path(env_override)

        candidates = [
            pickle_path.parent / "word_vazn_metadata.json",
            pickle_path.parent.parent / "aruuz" / "database" / "word_vazn_metadata.json",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[0]

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

    @staticmethod
    def _load_word_vazn_metadata(
        metadata_path: str | Path | None,
    ) -> Optional[dict[str, list[str]]]:
        """Load optional normalized-word -> list[vazn code] metadata."""
        if metadata_path is None:
            return None

        try:
            with open(metadata_path, encoding="utf-8") as fh:
                loaded = json.load(fh)
        except FileNotFoundError:
            return None
        except Exception:
            logging.getLogger(__name__).exception(
                "Failed to load word vazn metadata from %s", metadata_path
            )
            return None

        if not isinstance(loaded, dict):
            logging.getLogger(__name__).warning(
                "Ignoring word vazn metadata from %s because the top-level JSON value is not an object",
                metadata_path,
            )
            return None

        out: dict[str, list[str]] = {}
        for key, value in loaded.items():
            if not isinstance(key, str) or not isinstance(value, list):
                continue
            codes = [item.strip() for item in value if isinstance(item, str) and item.strip()]
            if codes:
                out[key] = list(dict.fromkeys(codes))
        return out

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
                query_vazn_codes=[],
                suffix_lengths={"exact": 0, "close": 0, "open": 0},
                total_counts={"exact": 0, "close": 0, "open": 0},
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

        query_vazn_codes = self._get_query_vazn_codes(script_query)
        query_roman_tails = self._get_query_roman_tails(script_query)
        query_letter_count = len(script_query)
        self._enrich_matches(
            exact_matches, query_letter_count, query_vazn_codes, query_roman_tails
        )
        self._enrich_matches(
            close_matches, query_letter_count, query_vazn_codes, query_roman_tails
        )
        self._enrich_matches(
            open_matches, query_letter_count, query_vazn_codes, query_roman_tails
        )

        self._sort_matches(exact_matches)
        self._sort_matches(close_matches)
        self._sort_matches(open_matches, prioritize_roman_tail2=True)

        total_counts = {
            "exact": len(exact_matches),
            "close": len(close_matches),
            "open": len(open_matches),
        }

        if limit is not None:
            exact_matches = exact_matches[:limit]
            close_matches = close_matches[:limit]
            open_matches = open_matches[:limit]

        return KafiyaResult(
            query=script_query,
            query_vazn_codes=query_vazn_codes,
            suffix_lengths=suffix_lengths,
            total_counts=total_counts,
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
        query_vazn_codes: List[str],
        query_roman_tails: dict[str, Optional[str]],
    ) -> None:
        """Attach metadata and ranking features used by the dictionary UI."""
        for match in matches:
            match.is_compound = "_" in match.word or " " in match.word
            lookup_word = match.word.replace("_", " ")
            normalized_lookup_word = normalize_urdu_text(lookup_word)
            match.same_letter_count = len(normalized_lookup_word) == query_letter_count
            match.vazn_codes = self._get_vazn_codes_for_word(normalized_lookup_word)
            match.vazn_match = self._has_compatible_vazn(query_vazn_codes, match.vazn_codes)

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
            roman = entry.get("roman")
            if isinstance(roman, str) and roman.strip():
                match.roman = roman.strip()
                match.roman_tail3 = self._roman_tail(match.roman, 3)
                match.roman_tail2 = self._roman_tail(match.roman, 2)
                query_tail3 = query_roman_tails.get("tail3")
                query_tail2 = query_roman_tails.get("tail2")
                match.roman_tail3_match = (
                    query_tail3 is not None and match.roman_tail3 == query_tail3
                )
                match.roman_tail2_match = (
                    query_tail2 is not None and match.roman_tail2 == query_tail2
                )

    def _sort_matches(
        self,
        matches: List[KafiyaMatch],
        *,
        prioritize_roman_tail2: bool = False,
    ) -> None:
        """Sort candidates by poetic usefulness for dictionary browsing."""
        matches.sort(
            key=lambda match: (
                self._open_bucket_priority(match)
                if prioritize_roman_tail2
                else (0 if match.vazn_match else 1),
                match.is_compound,
                not match.same_letter_count,
                0 if match.match_kind == "script" else 1,
                match.frequency_rank is None,
                match.frequency_rank if match.frequency_rank is not None else 0,
                not bool(match.meaning),
                match.word,
            )
        )

    def _open_bucket_priority(self, match: KafiyaMatch) -> int:
        """
        Rank only open-bucket matches with conservative Roman-tail boosting:
        tail3+vazn, tail2+vazn, vazn-only, tail3-only, tail2-only, fallback.
        """
        if match.vazn_match and match.roman_tail3_match:
            return 0
        if match.vazn_match and match.roman_tail2_match:
            return 1
        if match.vazn_match:
            return 2
        if match.roman_tail3_match:
            return 3
        if match.roman_tail2_match:
            return 4
        return 5

    def _get_query_vazn_codes(self, query_word: str) -> List[str]:
        scanned = Words()
        scanned.word = query_word
        scanned.taqti = []
        scanned = self._scanner.assign_scansion_to_word(scanned)
        raw_codes = [code.strip() for code in scanned.code if isinstance(code, str)]
        non_empty_codes = [code for code in raw_codes if code]
        return list(dict.fromkeys(non_empty_codes))

    def _normalize_roman_for_tail(self, roman: str) -> str:
        """
        Conservative Roman normalization for tail matching.

        Only enforces ii/ee equivalence and strips non-alphanumeric chars.
        """
        normalized = re.sub(r"[^a-z0-9]", "", roman.lower())
        normalized = normalized.replace("ee", "ii")
        return normalized

    def _roman_tail(self, roman: str, length: int) -> Optional[str]:
        """Return normalized Roman-Urdu tail of requested length when available."""
        normalized = self._normalize_roman_for_tail(roman)
        if len(normalized) < length:
            return None
        return normalized[-length:]

    def _get_query_roman_tails(self, script_query: str) -> dict[str, Optional[str]]:
        """Read query Roman metadata and return comparable tail tokens."""
        if not self._word_metadata:
            return {"tail3": None, "tail2": None}
        entry = self._word_metadata.get(script_query)
        if not isinstance(entry, dict):
            return {"tail3": None, "tail2": None}
        roman = entry.get("roman")
        if not isinstance(roman, str) or not roman.strip():
            return {"tail3": None, "tail2": None}
        return {
            "tail3": self._roman_tail(roman, 3),
            "tail2": self._roman_tail(roman, 2),
        }

    def _get_vazn_codes_for_word(self, normalized_lookup_word: str) -> List[str]:
        direct = self._word_vazn_metadata.get(normalized_lookup_word)
        if isinstance(direct, list):
            return direct

        fallback_key = normalized_lookup_word.replace(" ", "_")
        fallback = self._word_vazn_metadata.get(fallback_key)
        if isinstance(fallback, list):
            return fallback
        return []

    def _is_compatible_vazn_code_pair(self, query_code: str, candidate_code: str) -> bool:
        """Match vazn codes with x treated as flexible on either side."""
        if len(query_code) != len(candidate_code):
            return False

        for qch, cch in zip(query_code, candidate_code):
            if qch == "x" or cch == "x":
                continue
            if qch != cch:
                return False
        return True

    def _has_compatible_vazn(
        self,
        query_codes: List[str],
        candidate_codes: List[str],
    ) -> bool:
        if not query_codes or not candidate_codes:
            return False
        for query_code in query_codes:
            for candidate_code in candidate_codes:
                if self._is_compatible_vazn_code_pair(query_code, candidate_code):
                    return True
        return False

    def _fetch_bucket(
        self,
        phonetic_query: str,
        script_query: str,
        suffix_len: int,
        exclude: set[str],
    ) -> List[KafiyaMatch]:
        """
        Return index words that share a *phonetic* suffix of length *suffix_len* with
        the query, dropping *exclude* (the query and any words from stronger buckets).

        For *suffix_len* == 1 (the "open" bucket), the index key is the last character
        of *phonetic_query* (``full_normalize``; homophones share a bucket). Each
        candidate must also pass ``_passes_open_guard``, which compares the
        penultimate *script* letter class (vowel / semi_vowel / non_vowel) to cut
        spurious 1-letter matches. The open bucket is high recall, not full qāfiya.
        """
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
