# -*- coding: utf-8 -*-
"""
Meter alignment utilities: resolve meter pattern from fuzzy result, run align over
four meter variations, return best (distance, edit_ops, leverage).

Used by islah API and run_exact_vs_fuzzy script.
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from aruuz.models import LineScansionResultFuzzy

from aruuz.utils.aligner import align


def meter_pattern_for_fuzzy_result(so: "LineScansionResultFuzzy") -> Optional[str]:
    """
    Resolve meter pattern string from a LineScansionResultFuzzy, or None for
    special meters (e.g. Hindi/Zamzama) or unknown.
    """
    from aruuz.meters import (
        METERS,
        METERS_VARIED,
        RUBAI_METERS,
        RUBAI_METER_NAMES,
        NUM_METERS,
        NUM_VARIED_METERS,
    )

    mid = so.id
    if 0 <= mid < NUM_METERS:
        return METERS[mid]
    if NUM_METERS <= mid < NUM_METERS + NUM_VARIED_METERS:
        return METERS_VARIED[mid - NUM_METERS]
    if mid == -2:
        base = (so.meter_name or "").replace(" (رباعی)", "").strip()
        for idx, name in enumerate(RUBAI_METER_NAMES):
            if name == base:
                return RUBAI_METERS[idx]
        return None
    return None  # special meters (id < -2) or unknown


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
