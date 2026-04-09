"""
Strict Urdu-script radeef detection (MVP, single-file module).

Scope:
- Raw multiline text input.
- Urdu-script only checks.
- Strict mode only (exact normalized suffix matching).
- JSON-like dict output with both pass/fail and detailed diagnostics.

Implementation notes:
- Diacritic removal follows existing behavior in `aruuz.utils.araab.remove_araab`.
- Character canonicalization and punctuation cleanup are adapted from existing
  Urdu text-cleaning conventions used in `aruuz.utils.text`.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional, Sequence, Tuple

from aruuz.utils.araab import remove_araab


_URDU_BLOCK_RE = re.compile(r"[\u0600-\u06FF]")
_MULTISPACE_RE = re.compile(r"\s+")

# Canonicalization map for common Arabic/Urdu variants.
_CHAR_MAP = {
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ہ",
    "ۀ": "ہ",
    "ھ": "ہ",
    "ؤ": "و",
    "أ": "ا",
    "إ": "ا",
    "ٱ": "ا",
}

# End punctuation/noise only (strict radeef matching works on line endings).
_TRAILING_STRIP_CHARS = " ,\"'*۔،?!ؔ؟‘()؛;\u200B\u200C\u200D\uFEFF.ؒ؎=ؑؓ\uFDFD\uFDFA:’[]{}"

# Optional stoplist for trivial single-token candidates in strict MVP.
_TRIVIAL_SINGLE_TOKEN_STOPLIST = {"ہے"}


def _normalize_line(line: str) -> str:
    """Normalize one Urdu line for strict suffix comparison."""
    if not line:
        return ""

    text = unicodedata.normalize("NFC", line)
    text = remove_araab(text)
    text = text.translate(str.maketrans(_CHAR_MAP))

    # Align with existing text utility behavior:
    # ا + madd (\u0653) -> آ and ہ with hamza above normalization.
    text = re.sub("(\u0627)(\u0653)", "آ", text)
    text = re.sub("(\u06C2)", "\u06C1\u0654", text)

    text = text.strip()
    text = text.rstrip(_TRAILING_STRIP_CHARS)
    text = _MULTISPACE_RE.sub(" ", text).strip()
    return text


def _split_non_empty_lines(raw_text: str) -> List[Tuple[int, str]]:
    """Return (1-based line_number, original_line) for non-empty lines."""
    out: List[Tuple[int, str]] = []
    for idx, raw_line in enumerate(raw_text.splitlines(), start=1):
        trimmed = raw_line.strip()
        if trimmed:
            out.append((idx, trimmed))
    return out


def _assign_relevant_positions(total_lines: int) -> List[int]:
    """
    Relevant positions in the filtered non-empty line list (0-based):
    - first and second line
    - then every even-numbered line (2,4,6...) in 1-based human indexing.
    """
    if total_lines <= 0:
        return []

    relevant: List[int] = []
    for pos in range(total_lines):
        line_number = pos + 1
        if line_number in (1, 2) or (line_number >= 3 and line_number % 2 == 0):
            relevant.append(pos)
    return relevant


def _contains_non_urdu_characters(text: str) -> bool:
    """True if line has Latin letters or digits (outside Urdu-script-only intent)."""
    for ch in text:
        if ch.isspace():
            continue
        if _URDU_BLOCK_RE.match(ch):
            continue
        if ch in _TRAILING_STRIP_CHARS:
            continue
        # Any visible non-Urdu character counts as warning-worthy.
        return True
    return False


def _suffix_candidates(tokens: Sequence[str], max_suffix_tokens: int) -> List[str]:
    """Generate suffix phrases from the end, shortest to longest."""
    limit = min(len(tokens), max_suffix_tokens)
    return [" ".join(tokens[-n:]) for n in range(1, limit + 1)]


def _is_trivial_candidate(candidate: str) -> bool:
    toks = candidate.split()
    return len(toks) == 1 and toks[0] in _TRIVIAL_SINGLE_TOKEN_STOPLIST


def _candidate_score(candidate: str, coverage: int) -> Tuple[int, int, int, str]:
    toks = candidate.split()
    return (coverage, len(toks), len(candidate), candidate)


def _detect_best_candidate(
    relevant_normalized_lines: Sequence[str], max_suffix_tokens: int
) -> Dict[str, Any]:
    """
    Detect best suffix candidate across relevant lines.
    Returns selected candidate details and candidate leaderboard.
    """
    if not relevant_normalized_lines:
        return {"selected": None, "candidates": []}

    counts: Dict[str, int] = {}
    for line in relevant_normalized_lines:
        toks = line.split()
        if not toks:
            continue
        unique_cands = set(_suffix_candidates(toks, max_suffix_tokens))
        for c in unique_cands:
            counts[c] = counts.get(c, 0) + 1

    leaderboard: List[Dict[str, Any]] = []
    for phrase, coverage in counts.items():
        leaderboard.append(
            {
                "phrase": phrase,
                "coverage": coverage,
                "tokens": len(phrase.split()),
                "chars": len(phrase),
                "trivial": _is_trivial_candidate(phrase),
            }
        )

    leaderboard.sort(
        key=lambda x: (
            x["coverage"],
            x["tokens"],
            x["chars"],
            x["phrase"],
        ),
        reverse=True,
    )

    non_trivial = [c for c in leaderboard if not c["trivial"]]
    selected = non_trivial[0] if non_trivial else (leaderboard[0] if leaderboard else None)
    return {"selected": selected, "candidates": leaderboard}


def _build_line_results(
    original_non_empty_lines: Sequence[Tuple[int, str]],
    normalized_lines: Sequence[str],
    relevant_positions: Sequence[int],
    detected_radeef: Optional[str],
) -> Tuple[List[Dict[str, Any]], int, int]:
    relevant_set = set(relevant_positions)
    results: List[Dict[str, Any]] = []
    passed = 0
    failed = 0

    for pos, (original_idx, original_text) in enumerate(original_non_empty_lines):
        normalized = normalized_lines[pos]
        is_relevant = pos in relevant_set
        role = "relevant" if is_relevant else "non_relevant"

        entry: Dict[str, Any] = {
            "line_number": original_idx,
            "role": role,
            "original": original_text,
            "normalized": normalized,
            "matched_radeef": None,
            "pass": True if not is_relevant else False,
            "reason": "not_checked" if not is_relevant else "missing_radeef_at_end",
        }

        if is_relevant:
            if detected_radeef and normalized.endswith(detected_radeef):
                entry["matched_radeef"] = detected_radeef
                entry["pass"] = True
                entry["reason"] = "exact_suffix_match"
                passed += 1
            else:
                failed += 1

        results.append(entry)

    return results, passed, failed


def check_radeef(
    text: str,
    *,
    mode: str = "strict",
    max_suffix_tokens: int = 6,
) -> Dict[str, Any]:
    """
    Detect and validate radeef for Urdu ghazal text (strict MVP).

    Args:
        text: Raw multiline Urdu text.
        mode: Must be "strict" in MVP.
        max_suffix_tokens: Max token length used for suffix candidate generation.

    Returns:
        JSON-like dict with pass/fail and diagnostics.
    """
    warnings: List[str] = []
    errors: List[str] = []

    if mode != "strict":
        errors.append("unsupported_mode")
        return {
            "pass": False,
            "mode": mode,
            "script": "urdu",
            "detected_radeef": None,
            "confidence": 0.0,
            "summary": {
                "total_input_lines": len(text.splitlines()),
                "non_empty_lines": 0,
                "relevant_lines": 0,
                "relevant_lines_passed": 0,
                "relevant_lines_failed": 0,
            },
            "diagnostics": {
                "structure": {"status": "error", "warnings": []},
                "candidate_analysis": {
                    "top_candidates": [],
                    "selected_reason": "unsupported_mode",
                },
                "line_results": [],
            },
            "errors": errors,
            "warnings": warnings,
        }

    non_empty_lines = _split_non_empty_lines(text)
    normalized_lines = [_normalize_line(line) for _, line in non_empty_lines]

    if any(_contains_non_urdu_characters(line) for _, line in non_empty_lines):
        warnings.append("non_urdu_characters_detected")

    total_input_lines = len(text.splitlines())
    non_empty_count = len(non_empty_lines)

    if non_empty_count < 2:
        errors.append("insufficient_lines")

    relevant_positions = _assign_relevant_positions(non_empty_count)
    relevant_lines = [normalized_lines[i] for i in relevant_positions if i < len(normalized_lines)]

    if len(relevant_lines) < 2:
        errors.append("insufficient_relevant_lines")

    if non_empty_count % 2 != 0:
        warnings.append("odd_line_count")

    candidate_info = _detect_best_candidate(relevant_lines, max_suffix_tokens=max_suffix_tokens)
    selected = candidate_info["selected"]
    top_candidates = candidate_info["candidates"][:10]

    detected_radeef: Optional[str] = selected["phrase"] if selected else None
    if detected_radeef and _is_trivial_candidate(detected_radeef):
        warnings.append("trivial_candidate_rejected_used_alternative")

    line_results, relevant_passed, relevant_failed = _build_line_results(
        non_empty_lines,
        normalized_lines,
        relevant_positions,
        detected_radeef,
    )

    # If multiple candidates tie exactly with the selected one, mark ambiguity.
    ambiguous = False
    if selected:
        s_key = _candidate_score(selected["phrase"], selected["coverage"])
        ties = [
            c
            for c in candidate_info["candidates"]
            if _candidate_score(c["phrase"], c["coverage"]) == s_key and c["phrase"] != selected["phrase"]
        ]
        ambiguous = len(ties) > 0
    if ambiguous:
        warnings.append("ambiguous_top_candidates")

    if not detected_radeef:
        errors.append("no_valid_radeef_candidate")

    structure_status = "ok" if not errors else "error"
    selected_reason = (
        "max_coverage_then_longest_suffix"
        if selected
        else "no_valid_radeef_candidate"
    )

    passed = (
        len(errors) == 0
        and len(relevant_positions) > 0
        and relevant_failed == 0
        and detected_radeef is not None
    )

    if not passed and detected_radeef and relevant_failed > 0 and "no_valid_radeef_candidate" in errors:
        errors.remove("no_valid_radeef_candidate")

    confidence = 0.0
    if selected and len(relevant_lines) > 0:
        confidence = selected["coverage"] / float(len(relevant_lines))
        if ambiguous:
            confidence = max(0.0, confidence - 0.1)

    return {
        "pass": passed,
        "mode": "strict",
        "script": "urdu",
        "detected_radeef": detected_radeef if passed or detected_radeef else None,
        "confidence": round(confidence, 3),
        "summary": {
            "total_input_lines": total_input_lines,
            "non_empty_lines": non_empty_count,
            "relevant_lines": len(relevant_positions),
            "relevant_lines_passed": relevant_passed,
            "relevant_lines_failed": relevant_failed,
        },
        "diagnostics": {
            "structure": {
                "status": structure_status,
                "warnings": [w for w in warnings if w in {"odd_line_count", "non_urdu_characters_detected"}],
            },
            "candidate_analysis": {
                "top_candidates": [
                    {"phrase": c["phrase"], "coverage": c["coverage"], "tokens": c["tokens"]}
                    for c in top_candidates
                ],
                "selected_reason": selected_reason,
            },
            "line_results": line_results,
        },
        "errors": errors,
        "warnings": warnings,
    }


__all__ = ["check_radeef"]

