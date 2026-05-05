# -*- coding: utf-8 -*-
"""
/api/meter/distance: POST JSON and compute edit distance of a line code against
a target meter pattern.
"""

from typing import Any, Dict, Optional

from flask import request

from aruuz.meters import (
    METERS,
    METERS_VARIED,
    RUBAI_METERS,
    RUBAI_METER_NAMES,
    NUM_METERS,
    NUM_VARIED_METERS,
    meter_index,
)
from aruuz.utils.meter_align import align_best, build_deviations


def _resolve_pattern_from_target(target: Dict[str, Any]) -> Optional[str]:
    """
    Resolve and return a concrete meter pattern string from a target descriptor.
    
    Checks the following sources (in order) and returns the first resolved pattern:
    - A non-empty "meter_pattern" string in the target.
    - A numeric "meter_id" that maps to METERS, METERS_VARIED, or the special rubai mapping (when meter_id == -2 and a matching "meter_name" is provided).
    - A non-empty "meter_name" that maps to an index via meter_index and then to METERS or METERS_VARIED.
    
    Parameters:
        target (Dict[str, Any]): Dictionary that may contain "meter_pattern" (str), "meter_id" (int), and/or "meter_name" (str).
    
    Returns:
        Optional[str]: Resolved meter pattern string if found, otherwise `None`.
    """
    pattern = target.get("meter_pattern")
    if isinstance(pattern, str) and pattern.strip():
        return pattern.strip()

    meter_id = target.get("meter_id")
    meter_name = target.get("meter_name")

    if isinstance(meter_id, int):
        if 0 <= meter_id < NUM_METERS:
            return METERS[meter_id]
        if NUM_METERS <= meter_id < NUM_METERS + NUM_VARIED_METERS:
            return METERS_VARIED[meter_id - NUM_METERS]
        if meter_id == -2 and isinstance(meter_name, str):
            base = meter_name.replace(" (رباعی)", "").strip()
            for i, n in enumerate(RUBAI_METER_NAMES):
                if n == base:
                    return RUBAI_METERS[i]
            return None

    if isinstance(meter_name, str) and meter_name.strip():
        idxs = meter_index(meter_name.strip())
        if not idxs:
            return None
        idx = idxs[0]
        if 0 <= idx < NUM_METERS:
            return METERS[idx]
        if NUM_METERS <= idx < NUM_METERS + NUM_VARIED_METERS:
            return METERS_VARIED[idx - NUM_METERS]

    return None


def handle(request):
    """
    Handle POST requests to compute edit distance, alignment, and deviations between a source meter code and a resolved target meter pattern.
    
    Validates input JSON and resolves the target pattern from `target.meter_pattern`, `target.meter_id`, or `target.meter_name`. On success returns a response object containing:
    - source_code: the validated, trimmed source string.
    - target: { meter_name: str, meter_id: int|None, meter_pattern: str } where `meter_pattern` has any "/" characters removed.
    - distance: numeric edit distance between source and resolved pattern.
    - alignment: { distance: same as top-level distance, edit_ops: list, leverage: numeric }.
    - deviations: deviations data structure derived from the alignment edit operations.
    
    Error responses:
    - 405 with {"error": "Method not allowed"} if the request method is not POST.
    - 400 with {"error": "..."} for malformed JSON, missing/invalid `source_code`, or when the target pattern cannot be resolved.
    """
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict):
        return ({"error": "JSON body must be an object"}, 400)

    source_code = data.get("source_code")
    if not isinstance(source_code, str) or not source_code.strip():
        return ({"error": "Field 'source_code' must be a non-empty string"}, 400)
    source_code = source_code.strip()

    target = data.get("target")
    if not isinstance(target, dict):
        target = {}

    target_pattern = _resolve_pattern_from_target(target)
    if not target_pattern:
        return ({"error": "Could not resolve target meter pattern"}, 400)

    distance, edit_ops, leverage = align_best(source_code, target_pattern)
    deviations = build_deviations(edit_ops)

    return {
        "source_code": source_code,
        "target": {
            "meter_name": target.get("meter_name", "") or "",
            "meter_id": target.get("meter_id", None),
            "meter_pattern": target_pattern.replace("/", ""),
        },
        "distance": distance,
        "alignment": {
            "distance": distance,
            "edit_ops": edit_ops,
            "leverage": leverage,
        },
        "deviations": deviations,
    }
