"""
Strict Urdu-script kafiya checking built to compose with check_radeef().
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple

from aruuz.rhyme.radeef import check_radeef
from aruuz.rhyme.text_utils import (
    extract_kafiya_key,
    full_normalize,
    get_last_token,
    is_kafiya_match,
    normalize_urdu_text,
    resolve_kafiya_reference,
    strip_suffix_phrase,
)

def _extract_kafiya_candidates(
    text: str, radeef_result: Dict[str, Any]
) -> Tuple[List[Tuple[int, int, str, str]], List[str], List[str]]:
    """
    Each candidate: (line_number, verse_index, full_line, kafiya_word).
    verse_index matches radeef line_results (1-based among non-empty lines).
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
    # First two relevant candidates define kafiya reference (matla behavior).
    line_no_1, verse_1, full_line_1, word_1 = candidates[0]
    line_no_2, verse_2, full_line_2, word_2 = candidates[1]

    script_word_1 = normalize_urdu_text(word_1)
    script_word_2 = normalize_urdu_text(word_2)
    ph_word_1 = full_normalize(word_1)
    ph_word_2 = full_normalize(word_2)
    unit_mode, reference_unit_phonetic = resolve_kafiya_reference(ph_word_1, ph_word_2)

    if unit_mode == "no_match" or not reference_unit_phonetic:
        return {
            "pass": False,
            "reference_unit_phonetic": "",
            "reference_unit_script": "",
            "unit_mode": "unknown",
            "results": [],
            "errors": ["no_common_kafiya_unit_in_matla"],
            "warnings": [],
        }

    reference_unit_script = extract_kafiya_key(script_word_1, unit_mode)
    second_unit_phonetic = extract_kafiya_key(ph_word_2, unit_mode)
    results: List[Dict[str, Any]] = [
        {
            "line_no": line_no_1,
            "verse_index": verse_1,
            "full_line": full_line_1,
            "word": script_word_1,
            "status": "reference",
            "reason": f"matla_reference_unit=-{reference_unit_phonetic}",
            "phonetic_unit": reference_unit_phonetic,
            "script_unit": reference_unit_script,
        },
        {
            "line_no": line_no_2,
            "verse_index": verse_2,
            "full_line": full_line_2,
            "word": script_word_2,
            "status": "reference",
            "reason": f"matla_reference_unit=-{reference_unit_phonetic}",
            "phonetic_unit": second_unit_phonetic,
            "script_unit": extract_kafiya_key(script_word_2, unit_mode),
        },
    ]

    matched = 0
    phonetic_matched = 0
    flagged = 0

    for line_no, verse_idx, full_line, raw_word in candidates[2:]:
        script_word = normalize_urdu_text(raw_word)
        ph_word = full_normalize(raw_word)
        actual_script_unit = extract_kafiya_key(script_word, unit_mode)
        actual_ph_unit = extract_kafiya_key(ph_word, unit_mode)

        if is_kafiya_match(reference_unit_script, unit_mode, script_word):
            status = "match"
            reason = f"script_unit_match=-{reference_unit_script}"
            matched += 1
        elif is_kafiya_match(reference_unit_phonetic, unit_mode, ph_word):
            status = "phonetic_match"
            reason = (
                f"phonetic_unit_match=-{reference_unit_phonetic};"
                f" script_unit=-{actual_script_unit}"
            )
            phonetic_matched += 1
        else:
            status = "flagged"
            reason = (
                f"kafiya_break expected_unit=-{reference_unit_phonetic}"
                f" got_unit=-{actual_ph_unit}"
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
                "phonetic_unit": actual_ph_unit,
                "script_unit": actual_script_unit,
            }
        )

    total_checked = max(0, len(candidates) - 2)
    return {
        "pass": flagged == 0,
        "reference_unit_phonetic": reference_unit_phonetic,
        "reference_unit_script": reference_unit_script,
        "unit_mode": unit_mode,
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
    """
    rr = radeef_result if isinstance(radeef_result, dict) else check_radeef(text, mode="strict")
    candidates, errors, warnings = _extract_kafiya_candidates(text, rr)

    if errors:
        return {
            "pass": False,
            "reference_unit_phonetic": "",
            "reference_unit_script": "",
            "unit_mode": "unknown",
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

