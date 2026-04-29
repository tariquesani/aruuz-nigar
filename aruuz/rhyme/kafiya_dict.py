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
        """
        Initialize a KafiyaMatch representing a candidate rhyme with provenance and optional enrichments.
        
        Parameters:
            word (str): The candidate word as stored in the dictionary index.
            match_kind (MatchKind): The provenance of the match; typically "script" when script suffixes match or "phonetic" when only phonetic suffixes match.
            meaning (Optional[str]): Human-readable meaning for the candidate, if available.
            frequency_rank (Optional[int]): Lower values indicate higher corpus frequency; used for ranking when present.
            is_compound (bool): True if the candidate appears to be a compound (contains space or underscore).
            same_letter_count (bool): True if the candidate has the same script letter count as the query.
            vazn_codes (Optional[List[str]]): List of scansion/vazn codes associated with the candidate; defaults to an empty list.
            vazn_match (bool): True if at least one candidate vazn code is compatible with the query's vazn codes.
            roman (Optional[str]): Romanized form of the candidate (normalized), if available from metadata.
            roman_tail3 (Optional[str]): Last three characters of the normalized roman form, or None.
            roman_tail2 (Optional[str]): Last two characters of the normalized roman form, or None.
            roman_tail3_match (bool): True if `roman_tail3` matches the query's roman tail3.
            roman_tail2_match (bool): True if `roman_tail2` matches the query's roman tail2.
        """
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
        """
        Produce a concise, unambiguous representation of the KafiyaMatch for debugging.
        
        Returns:
            A string formatted as KafiyaMatch(<word>, <match_kind>) where <word> and <match_kind> are the object's stored values.
        """
        return f"KafiyaMatch({self.word!r}, {self.match_kind!r})"

    def to_dict(self) -> Dict:
        """
        Serialize the match into a JSON-serializable dictionary including only populated fields.
        
        The returned mapping always contains:
        - "word": the candidate word as stored.
        - "match_kind": provenance, either "script" or "phonetic".
        - "is_compound": whether the word appears compound (contains space or underscore).
        - "same_letter_count": whether the candidate has the same script letter count as the query.
        - "vazn_match": whether any vazn (scansion) code of the candidate is compatible with the query.
        
        The dictionary conditionally contains the following keys only when present on the match:
        - "vazn_codes": list of vazn codes for the candidate.
        - "meaning": human-readable meaning from word metadata.
        - "frequency_rank": integer frequency rank when available.
        - "roman": normalized Roman-Urdu form from metadata.
        - "roman_tail3", "roman_tail2": last 3/2 characters of the normalized roman form (if available).
        - "roman_tail3_match", "roman_tail2_match": boolean flags indicating tail matches against the query.
        
        Returns:
            dict: A dictionary representation of the match suitable for downstream serialization.
        """
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
        """
        Initialize a KafiyaResult that bundles lookup input, bucketed matches, and summary statistics.
        
        Parameters:
        	query (str): Normalized query word in script form.
        	query_vazn_codes (List[str]): Scansion/vazn codes identified for the query (deduplicated, in order).
        	suffix_lengths (Dict[str, int]): Mapping of bucket names ("exact", "close", "open") to the suffix length used for that bucket.
        	total_counts (Dict[str, int]): Total number of candidate matches found per bucket before any per-bucket limiting.
        	exact (List[KafiyaMatch]): Matches classified as exact (longest shared suffix).
        	close (List[KafiyaMatch]): Matches classified as close (medium-length shared suffix).
        	open_ (List[KafiyaMatch]): Matches classified as open (one-letter suffix) — trailing underscore distinguishes the parameter name from the reserved word.
        """
        self.query = query
        self.query_vazn_codes = query_vazn_codes
        self.suffix_lengths = suffix_lengths
        self.total_counts = total_counts
        self.exact = exact
        self.close = close
        self.open = open_

    def to_dict(self) -> Dict:
        """
        Serialize the KafiyaResult into a plain dictionary for external consumption.
        
        Returns:
            result (Dict): A mapping with the following keys:
                - "query": The normalized script form of the original query.
                - "query_vazn_codes": List[str] of scanned vazn codes for the query (may be empty).
                - "suffix_lengths": Dict[str, int] mapping bucket names to the suffix length used.
                - "total_counts": Dict[str, int] mapping bucket names to the total number of matches before limiting.
                - "exact": List[Dict] serialized `KafiyaMatch` objects for the exact bucket.
                - "close": List[Dict] serialized `KafiyaMatch` objects for the close bucket.
                - "open": List[Dict] serialized `KafiyaMatch` objects for the open bucket.
        """
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
        """
        Initialize a KafiyaDict lookup engine with a precomputed suffix index and optional metadata.
        
        Parameters:
            index (dict): Mapping keyed by (suffix_length, phonetic_suffix) to sets of candidate words used for suffix lookups.
            word_metadata (Optional[dict[str, dict[str, object | None]]]): Optional per-word metadata (meaning, frequency, roman, etc.) keyed by normalized script form.
            word_vazn_metadata (Optional[dict[str, list[str]]]): Optional mapping of normalized words to lists of vazn (scansion) codes.
            max_per_bucket (Optional[int]): Default maximum number of candidates to return per quality bucket; use None for no limit.
        """
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
        """
        Load a KafiyaDict from a serialized suffix index file and optional metadata.
        
        Loads the index pickle at `pickle_path`, optionally loads word metadata and word-vazn metadata (resolving a default vazn metadata path when `vazn_metadata_path` is None), and returns a configured KafiyaDict instance.
        
        Parameters:
            pickle_path (str | Path): Path to the pickle file containing the pre-built suffix index.
            metadata_path (str | Path | None): Optional path to a JSON file with word metadata; if None, no word metadata is loaded.
            vazn_metadata_path (str | Path | None): Optional path to a JSON file with word vazn metadata; if None, a candidate path is resolved automatically.
            max_per_bucket (Optional[int]): Default maximum number of matches to return per bucket when performing lookups.
        
        Returns:
            KafiyaDict: An instance initialized with the loaded index and any loaded metadata.
        """
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
        Locate the word_vazn_metadata.json file related to the given index pickle path.
        
        Search order (first match is returned):
        1. Path from the WORD_VAZN_METADATA_PATH environment variable (if set).
        2. A sibling file next to the provided pickle path: `<pickle_path.parent>/word_vazn_metadata.json`.
        3. A repository-level fallback: `<pickle_path.parent.parent>/aruuz/database/word_vazn_metadata.json`.
        If none of the candidate files exist, the sibling path (item 2) is returned as the default.
        
        Parameters:
            pickle_path (Path): Path to the index pickle file used as the anchor for locating metadata.
        
        Returns:
            Path: The chosen metadata file path (existing file when found, otherwise the sibling candidate).
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
        """
        Load word metadata from a JSON file for enriching lookup results.
        
        Parameters:
            metadata_path (str | Path | None): Path to a JSON file containing a mapping
                from normalized words to metadata objects. If `None`, no metadata is loaded.
        
        Returns:
            Optional[dict[str, dict[str, object | None]]]: The loaded mapping when the file
            exists and the top-level JSON value is an object; otherwise `None` (returned
            when `metadata_path` is `None`, the file is missing, the top-level JSON is not
            an object, or an error occurs while loading).
        """
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
        """
        Load a mapping from normalized words to lists of vazn codes from a JSON file.
        
        If `metadata_path` is None or the file does not exist or cannot be parsed, returns `None`.
        On success returns a dict where each key is a string (normalized word) and each value is a list
        of non-empty, whitespace-trimmed vazn code strings. Codes are deduplicated while preserving
        their original order. Entries whose key is not a string or whose value is not a list are ignored;
        within each list, only string items that remain non-empty after trimming are kept.
        """
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
        Return candidate kafiya matches for a query, grouped into three quality buckets: exact, close, and open.
        
        Parameters:
        	query (str): The input word in any orthography to search for kafiya.
        	max_per_bucket (Optional[int]): If provided, limit the number of returned matches per bucket.
        
        Returns:
        	KafiyaResult: Result object containing:
        		- the normalized script query,
        		- `query_vazn_codes`: scansion codes computed for the query,
        		- `suffix_lengths`: chosen suffix lengths for each bucket (`exact`, `close`, `open`),
        		- `total_counts`: counts found per bucket before applying `max_per_bucket`,
        		- `exact`, `close`, `open_`: lists of `KafiyaMatch` objects for each bucket.
        		If the query is too short to produce suffixes, returns a `KafiyaResult` with empty buckets and zeroed statistics.
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
        Decide whether a candidate with a 1-letter suffix is allowed based on penultimate-letter compatibility.
        
        Rejects if either word has fewer than two characters. Classifies the penultimate script letter of each word (vowel, semi_vowel, or non_vowel) and permits the candidate only when its class is compatible with the query's class (semi-vowels bridge vowel and non-vowel classes to allow common Urdu rhyme spellings).
        
        Returns:
            `true` if the candidate's penultimate-letter class is compatible with the query's, `false` otherwise.
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
        """
        Enrich each KafiyaMatch in `matches` with metadata and ranking flags used by the UI.
        
        Parameters:
            matches (List[KafiyaMatch]): Mutable list of matches to update in-place.
            query_letter_count (int): Number of letters in the normalized query script form; used to set `same_letter_count`.
            query_vazn_codes (List[str]): Vazn codes computed for the query; used to populate `vazn_match`.
            query_roman_tails (dict[str, Optional[str]]): Dict with keys `"tail3"` and `"tail2"` containing the query's normalized Roman tails or `None`; used to compute roman-tail match flags.
        
        Side effects:
            For each match sets or updates these attributes:
              - is_compound
              - same_letter_count
              - vazn_codes
              - vazn_match
              - meaning (if available in word metadata)
              - frequency_rank (if available)
              - roman, roman_tail3, roman_tail2 (if available)
              - roman_tail3_match, roman_tail2_match (if query tails are present)
        """
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
        """
        Sort candidate matches in-place to prioritize most useful poetic rhymes for browsing.
        
        When `prioritize_roman_tail2` is False the primary sort favors matches with compatible vazn codes; when True the primary sort uses an open-bucket priority that elevates combinations of vazn and Roman-tail matches. Subsequent tie-breakers (in order) prefer:
        - non-compound words over compound words,
        - candidates whose letter count equals the query's,
        - script-suffix matches over phonetic-only matches,
        - entries that have a frequency rank (and lower numeric ranks first),
        - entries that have a recorded meaning,
        - finally lexicographic order of the candidate word.
        
        Parameters:
            matches: List of KafiyaMatch objects to sort in-place.
            prioritize_roman_tail2: If True, use the open-bucket priority that gives extra weight to Roman-tail2/3 and vazn combinations; otherwise prioritize simple vazn compatibility.
        """
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
        Assign a priority rank for open-bucket matches based on vazn and Roman-tail matches.
        
        Lower values indicate higher priority when sorting open-bucket candidates; the ranking favors combined vazn+roman-tail matches, then vazn-only, then roman-tail-only, then neither.
        
        Returns:
            priority (int): Priority code where
                0 = both vazn match and 3-character roman tail match,
                1 = vazn match and 2-character roman tail match,
                2 = vazn match only,
                3 = 3-character roman tail match only,
                4 = 2-character roman tail match only,
                5 = neither match.
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
        """
        Extract the unique scansion (vazn) codes for a query word.
        
        Assigns scansion to the provided word, collects string codes with surrounding whitespace removed,
        drops empty entries, preserves the original order, and removes duplicate codes.
        
        Returns:
            List[str]: Vazn code strings in original order with whitespace trimmed and duplicates removed.
        """
        scanned = Words()
        scanned.word = query_word
        scanned.taqti = []
        scanned = self._scanner.assign_scansion_to_word(scanned)
        raw_codes = [code.strip() for code in scanned.code if isinstance(code, str)]
        non_empty_codes = [code for code in raw_codes if code]
        return list(dict.fromkeys(non_empty_codes))

    def _normalize_roman_for_tail(self, roman: str) -> str:
        """
        Normalize a Romanized Urdu string for tail comparison.
        
        Parameters:
            roman (str): Romanized form of a word.
        
        Returns:
            str: Lowercased string with non-alphanumeric characters removed and "ee" normalized to "ii".
        """
        normalized = re.sub(r"[^a-z0-9]", "", roman.lower())
        normalized = normalized.replace("ee", "ii")
        return normalized

    def _roman_tail(self, roman: str, length: int) -> Optional[str]:
        """
        Get the last `length` characters of the input Roman-Urdu string after normalization.
        
        Returns:
            tail (Optional[str]): The last `length` characters of the normalized Roman-Urdu string, or `None` if the normalized string has fewer than `length` characters.
        """
        normalized = self._normalize_roman_for_tail(roman)
        if len(normalized) < length:
            return None
        return normalized[-length:]

    def _get_query_roman_tails(self, script_query: str) -> dict[str, Optional[str]]:
        """
        Obtain normalized Roman-tail tokens for the query word to enable tail-based comparisons.
        
        Parameters:
            script_query (str): Normalized Urdu script form of the query used as a lookup key in the word metadata.
        
        Returns:
            dict[str, Optional[str]]: A mapping with keys "tail3" and "tail2" whose values are the last 3 and last 2 characters of the normalized Roman transliteration respectively, or `None` for each when no valid Roman form is available.
        """
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
        """
        Retrieve the vazn (scansion) codes for a normalized lookup word.
        
        Parameters:
            normalized_lookup_word (str): The normalized lookup form of the word (spaces preserved). A fallback with spaces replaced by underscores is attempted if the direct key is not present.
        
        Returns:
            List[str]: A list of vazn code strings for the word if found; otherwise an empty list.
        """
        direct = self._word_vazn_metadata.get(normalized_lookup_word)
        if isinstance(direct, list):
            return direct

        fallback_key = normalized_lookup_word.replace(" ", "_")
        fallback = self._word_vazn_metadata.get(fallback_key)
        if isinstance(fallback, list):
            return fallback
        return []

    def _is_compatible_vazn_code_pair(self, query_code: str, candidate_code: str) -> bool:
        """
        Determine whether two vazn codes are compatible, treating the character `'x'` in either code as a wildcard that matches any character.
        
        Parameters:
            query_code (str): Vazn code for the query; must be the same length as candidate_code.
            candidate_code (str): Vazn code for the candidate; must be the same length as query_code.
        
        Returns:
            `true` if both codes have equal length and every position either matches exactly or contains `'x'` in at least one code, `false` otherwise.
        """
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
        """
        Determine whether any vazn code from the query is compatible with any vazn code from the candidate.
        
        Parameters:
            query_codes (List[str]): Vazn codes derived for the query word.
            candidate_codes (List[str]): Vazn codes associated with the candidate word.
        
        Returns:
            `true` if at least one query code is compatible with a candidate code, `false` otherwise.
        
        Notes:
            Compatibility requires codes of equal length and allows the character `'x'` to act as a wildcard at any position.
        """
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
        Find candidate words that share a phonetic suffix of the given length with the query.
        
        Returns words from the precomputed suffix index that match the phonetic suffix taken from
        the end of `phonetic_query`, excluding any entries in `exclude`. For `suffix_len == 1`
        (the "open" bucket), candidates are additionally filtered by `_passes_open_guard` which
        compares penultimate script-letter classes to reduce spurious single-letter matches.
        
        Parameters:
            phonetic_query: The fully-normalized phonetic form of the query used to extract the suffix.
            script_query: The normalized script form of the query used for script-suffix comparison.
            suffix_len: Length of the suffix to match; if less than or equal to 0 an empty list is returned.
            exclude: Set of words to omit from results (e.g., the query and words already returned by stronger buckets).
        
        Returns:
            matches: List of `KafiyaMatch` objects for words that share the requested phonetic suffix,
            with `match_kind` set to `"script"` when the script suffix also matches, or `"phonetic"` otherwise.
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
