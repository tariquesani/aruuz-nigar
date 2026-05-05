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
    """Resolve target meter pattern from explicit pattern, id/name, or name."""
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
    Handle /api/meter/distance. POST only.
    Expects JSON:
      {
        "source_code": "-==-==",
        "target": { "meter_name": "...", "meter_id": 12, "meter_pattern": "...?" }
      }
    Returns distance/alignment/deviations against target meter pattern.
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
