# -*- coding: utf-8 -*-
"""
Meter alignment utilities: resolve meter pattern from fuzzy result, run align over
four meter variations, return best (distance, edit_ops, leverage).

Used by islah API and run_exact_vs_fuzzy script.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from aruuz.models import LineScansionResult, LineScansionResultFuzzy

from aruuz.utils.aligner import align, match_char


def _meter_pattern_from_id(mid: int, meter_name: str) -> Optional[str]:
    """
    Resolve meter pattern string from meter id and name.
    Shared by exact and fuzzy result helpers.
    """
    from aruuz.meters import (
        METERS,
        METERS_VARIED,
        RUBAI_METERS,
        RUBAI_METER_NAMES,
        NUM_METERS,
        NUM_VARIED_METERS,
    )

    if 0 <= mid < NUM_METERS:
        return METERS[mid]
    if NUM_METERS <= mid < NUM_METERS + NUM_VARIED_METERS:
        return METERS_VARIED[mid - NUM_METERS]
    if mid == -2:
        base = (meter_name or "").replace(" (رباعی)", "").strip()
        for idx, name in enumerate(RUBAI_METER_NAMES):
            if name == base:
                return RUBAI_METERS[idx]
        return None
    return None  # special meters (id < -2) or unknown


def meter_pattern_for_exact_result(so: "LineScansionResult") -> Optional[str]:
    """
    Resolve meter pattern string from a LineScansionResult (exact match), or None
    for special meters (e.g. Hindi/Zamzama) or unknown.
    """
    return _meter_pattern_from_id(so.id, so.meter_name)


def meter_pattern_for_fuzzy_result(so: "LineScansionResultFuzzy") -> Optional[str]:
    """
    Resolve meter pattern string from a LineScansionResultFuzzy, or None for
    special meters (e.g. Hindi/Zamzama) or unknown.
    """
    return _meter_pattern_from_id(so.id, so.meter_name)


def four_meter_variations(meter_pattern: str) -> List[str]:
    """Return four pattern variants: strip '/', then +/- and ~ combinations."""
    m = meter_pattern.replace("/", "")
    return [
        m.replace("+", ""),
        m.replace("+", "") + "~",
        m.replace("+", "~") + "~",
        m.replace("+", "~"),
    ]


def align_best(code: str, meter_pattern: str) -> Tuple[int, List[Dict[str, Any]], List[Tuple[int, int]]]:
    """
    Align code to meter by trying all four meter variations; return the best
    (distance, edit_ops, leverage).
    """
    best_dist: Optional[int] = None
    best_ops: List[Dict[str, Any]] = []
    best_lev: List[Tuple[int, int]] = []
    for v in four_meter_variations(meter_pattern):
        d, ops, lev = align(v, code)
        if best_dist is None or d < best_dist:
            best_dist = d
            best_ops = ops
            best_lev = lev
    assert best_dist is not None
    return (best_dist, best_ops, best_lev)


def build_deviations(
    edit_ops: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert align edit_ops into a list of deviation objects for guided correction.
    Each deviation has: type (substitute|insert|delete), code_pos, pattern_pos (if applicable),
    current (syllable in code), expected (syllable in pattern). Indices are 0-based.
    """
    deviations: List[Dict[str, Any]] = []
    for o in edit_ops:
        op = o.get("op")
        if op == "match":
            continue
        code_pos = o.get("code_pos", -1)
        pattern_pos = o.get("pattern_pos", -1)
        pattern_char = o.get("pattern_char")
        code_char = o.get("code_char")
        if op == "substitute":
            deviations.append({
                "type": "substitute",
                "code_pos": code_pos,
                "pattern_pos": pattern_pos,
                "current": code_char,
                "expected": pattern_char,
            })
        elif op == "insert":
            deviations.append({
                "type": "insert",
                "code_pos": code_pos,
                "pattern_pos": pattern_pos,
                "current": None,
                "expected": pattern_char,
            })
        elif op == "delete":
            deviations.append({
                "type": "delete",
                "code_pos": code_pos,
                "pattern_pos": -1,
                "current": code_char,
                "expected": None,
            })
    return deviations


def _match_code_prefix(code: str, start: int, pattern: str) -> bool:
    """
    True if code[start:start+len(pattern)] matches pattern under x/~ rules.
    (pattern char vs code char: match_char(pattern[i], code[start+i]).)
    """
    n = len(pattern)
    if start + n > len(code):
        return False
    for i in range(n):
        if not match_char(pattern[i], code[start + i]):
            return False
    return True


def deduce_foot_segments(code: str) -> List[Dict[str, Any]]:
    """
    Segment code into feet by greedy longest-match from the start.
    Uses known foot patterns and x/~ rules. Returns list of
    { "foot": foot name, "code": matched slice, "start": int, "end": int }.
    """
    from aruuz.meters import FEET, FEET_NAMES

    # Sort by pattern length descending so we try longer feet first
    foot_list = sorted(zip(FEET, FEET_NAMES), key=lambda x: -len(x[0]))
    segments: List[Dict[str, Any]] = []
    start = 0
    while start < len(code):
        matched = False
        for pat, name in foot_list:
            if _match_code_prefix(code, start, pat):
                end = start + len(pat)
                segments.append({
                    "foot": name,
                    "code": code[start:end],
                    "start": start,
                    "end": end,
                })
                start = end
                matched = True
                break
        if not matched:
            break
    return segments


def word_boundaries_from_taqti(word_taqti: List[str]) -> List[Dict[str, Any]]:
    """
    Build list of { word_index, code_start, code_end } from word_taqti.
    code_end is exclusive (Python slice style).
    """
    boundaries: List[Dict[str, Any]] = []
    start = 0
    for i, code in enumerate(word_taqti):
        end = start + len(code)
        boundaries.append({"word_index": i, "code_start": start, "code_end": end})
        start = end
    return boundaries
