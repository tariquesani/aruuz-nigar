"""
Strict Urdu-script kafiya checking built to compose with check_radeef().
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from aruuz.rhyme.radeef import check_radeef
from aruuz.rhyme.text_utils import (
    get_last_token,
    normalize_urdu_text,
    strip_suffix_phrase,
)

PHONETIC_MAP = {
    "ث": "س",
    "ص": "س",
    "ذ": "ز",
    "ض": "ز",
    "ظ": "ز",
    "ح": "ہ",
    "ط": "ت",
}
"""Script-level substitutions used for phonetic kafiya comparison."""


def _phonetic_normalize(word: str) -> str:
    """Map Urdu letters to simplified phonetic equivalents."""
    return "".join(PHONETIC_MAP.get(c, c) for c in word)


def _full_normalize_kafiya_word(word: str) -> str:
    """Normalize a kafiya word in script and then phonetic form."""
    return _phonetic_normalize(normalize_urdu_text(word))


def _longest_common_suffix_length(a: str, b: str) -> int:
    """
    Return the shared suffix length between two words.

    Full-word identity is intentionally avoided so kafiya is not inferred
    from exact repeated words alone.
    """
    ra, rb = a[::-1], b[::-1]
    common = 0
    for x, y in zip(ra, rb):
        if x != y:
            break
        common += 1
    # Avoid full-word identity as the only pattern.
    return min(common, len(a) - 1, len(b) - 1) if a and b else 0


def _suffix(word: str, length: int) -> str:
    """Safely return the last `length` characters from `word`."""
    if length <= 0:
        return ""
    return word[-length:] if len(word) >= length else word


def _extract_kafiya_candidates(
    text: str, radeef_result: Dict[str, Any]
) -> Tuple[List[Tuple[int, int, str, str]], List[str], List[str]]:
    """
    Extract candidate kafiya words from radeef-validated relevant lines.

    Each candidate: (line_number, verse_index, full_line, kafiya_word).
    verse_index matches radeef line_results (1-based among non-empty lines).

    Returns:
        A tuple of (candidates, errors, warnings).
    """
    errors: List[str] = []
    warnings: List[str] = []
    candidates: List[Tuple[int, int, str, str]] = []

    detected_radeef = radeef_result.get("detected_radeef")
    diag = radeef_result.get("diagnostics", {})
    line_results = diag.get("line_results", [])

    if not detected_radeef:
        errors.append("missing_radeef_for_kafiya")
        return candidates, errors, warnings

    if not isinstance(line_results, list):
        errors.append("invalid_radeef_line_results")
        return candidates, errors, warnings

    for entry in line_results:
        if not isinstance(entry, dict):
            continue
        if entry.get("role") != "relevant":
            continue

        line_no = int(entry.get("line_number", 0))
        verse_index = int(entry.get("verse_index", 0))
        original = str(entry.get("original", "")).strip()
        normalized = str(entry.get("normalized", "")).strip()

        if not normalized.endswith(detected_radeef):
            # We only evaluate kafiya where radeef is actually present.
            continue

        prefix = strip_suffix_phrase(normalized, detected_radeef)
        kafiya_word = get_last_token(prefix)
        if not kafiya_word:
            warnings.append(f"line_{line_no}_missing_kafiya_word")
            continue
        candidates.append((line_no, verse_index, original or normalized, kafiya_word))

    if len(candidates) < 2:
        errors.append("insufficient_kafiya_candidates")

    return candidates, errors, warnings


def _check_candidates(candidates: Sequence[Tuple[int, int, str, str]]) -> Dict[str, Any]:
    """
    Validate candidate words against a reference kafiya suffix.

    The first two candidates (matla) define the suffix reference. Remaining
    candidates are marked as script match, phonetic match, or flagged break.
    """
    # First two relevant candidates define kafiya reference (matla behavior).
    line_no_1, verse_1, full_line_1, word_1 = candidates[0]
    line_no_2, verse_2, full_line_2, word_2 = candidates[1]

    script_word_1 = normalize_urdu_text(word_1)
    script_word_2 = normalize_urdu_text(word_2)
    ph_word_1 = _full_normalize_kafiya_word(word_1)
    ph_word_2 = _full_normalize_kafiya_word(word_2)

    suffix_len = _longest_common_suffix_length(ph_word_1, ph_word_2)
    if suffix_len == 0:
        return {
            "pass": False,
            "reference_suffix_phonetic": "",
            "reference_suffix_script": "",
            "suffix_length": 0,
            "results": [],
            "errors": ["no_common_kafiya_suffix_in_matla"],
            "warnings": [],
        }

    reference_suffix_phonetic = _suffix(ph_word_1, suffix_len)
    reference_suffix_script = _suffix(script_word_1, suffix_len)
    results: List[Dict[str, Any]] = [
        {
            "line_no": line_no_1,
            "verse_index": verse_1,
            "full_line": full_line_1,
            "word": script_word_1,
            "status": "reference",
            "reason": f"matla_reference_suffix=-{reference_suffix_phonetic}",
        },
        {
            "line_no": line_no_2,
            "verse_index": verse_2,
            "full_line": full_line_2,
            "word": script_word_2,
            "status": "reference",
            "reason": f"matla_reference_suffix=-{reference_suffix_phonetic}",
        },
    ]

    matched = 0
    phonetic_matched = 0
    flagged = 0

    for line_no, verse_idx, full_line, raw_word in candidates[2:]:
        script_word = normalize_urdu_text(raw_word)
        ph_word = _full_normalize_kafiya_word(raw_word)
        actual_script_suffix = _suffix(script_word, suffix_len)
        actual_ph_suffix = _suffix(ph_word, suffix_len)

        if actual_script_suffix == reference_suffix_script:
            status = "match"
            reason = f"script_suffix_match=-{reference_suffix_script}"
            matched += 1
        elif actual_ph_suffix == reference_suffix_phonetic:
            status = "phonetic_match"
            reason = (
                f"phonetic_suffix_match=-{reference_suffix_phonetic};"
                f" script_suffix=-{actual_script_suffix}"
            )
            phonetic_matched += 1
        else:
            status = "flagged"
            reason = (
                f"kafiya_break expected_phonetic=-{reference_suffix_phonetic}"
                f" got_phonetic=-{actual_ph_suffix}"
            )
            flagged += 1

        results.append(
            {
                "line_no": line_no,
                "verse_index": verse_idx,
                "full_line": full_line,
                "word": script_word,
                "status": status,
                "reason": reason,
            }
        )

    total_checked = max(0, len(candidates) - 2)
    return {
        "pass": flagged == 0,
        "reference_suffix_phonetic": reference_suffix_phonetic,
        "reference_suffix_script": reference_suffix_script,
        "suffix_length": suffix_len,
        "summary": {
            "candidate_lines": len(candidates),
            "checked_lines": total_checked,
            "matches": matched,
            "phonetic_matches": phonetic_matched,
            "flagged": flagged,
        },
        "results": results,
        "errors": [],
        "warnings": [],
    }


def check_kafiya(
    text: str,
    *,
    radeef_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Check kafiya by consuming check_radeef output plus original text.

    Args:
        text: Raw multiline ghazal text.
        radeef_result: Optional precomputed check_radeef(...) result.
                       If absent, this function computes it.

    Returns:
        A diagnostics dictionary including pass/fail, detected reference
        suffixes, per-line status, summary counts, and warnings/errors.
    """
    rr = radeef_result if isinstance(radeef_result, dict) else check_radeef(text, mode="strict")
    candidates, errors, warnings = _extract_kafiya_candidates(text, rr)

    if errors:
        return {
            "pass": False,
            "reference_suffix_phonetic": "",
            "reference_suffix_script": "",
            "suffix_length": 0,
            "summary": {
                "candidate_lines": len(candidates),
                "checked_lines": 0,
                "matches": 0,
                "phonetic_matches": 0,
                "flagged": 0,
            },
            "results": [],
            "errors": errors,
            "warnings": warnings,
        }

    out = _check_candidates(candidates)
    out["warnings"] = list(set(out.get("warnings", []) + warnings))
    return out


__all__ = ["check_kafiya"]

