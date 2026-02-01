# -*- coding: utf-8 -*-
"""
/api/meter/dominant: POST JSON with results list; resolve dominant meter.
Returns a single object with as much meter information as is available.
"""

import logging
from flask import request

from aruuz.meters import meter_index, meter_roman
from aruuz.models import LineScansionResult
from aruuz.scansion.scoring import MeterResolver

logger = logging.getLogger(__name__)


def handle(request):
    """
    Handle /api/meter/dominant. POST only.
    Expects JSON: { "results": [ { "meter_name": "...", "feet": "..." }, ... ] }
    Returns: single object { meter_name, meter_roman?, id?, feet, is_dominant } for the dominant meter.
    """
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    data = request.get_json(force=True, silent=True)
    if not isinstance(data, dict) or "results" not in data:
        return ({"error": "JSON body must contain 'results' array"}, 400)

    raw = data["results"]
    if not isinstance(raw, list):
        return ({"error": "'results' must be an array"}, 400)

    # Build LineScansionResult list (only meter_name and feet needed for resolve_dominant_meter)
    results = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            return ({"error": f"results[{i}] must be an object with meter_name and feet"}, 400)
        meter_name = item.get("meter_name")
        feet = item.get("feet")
        if meter_name is None or feet is None:
            return ({"error": f"results[{i}] must have 'meter_name' and 'feet'"}, 400)
        so = LineScansionResult(meter_name=str(meter_name).strip(), feet=str(feet).strip())
        results.append(so)

    if not results:
        return ({}, 200)

    dominant_list = MeterResolver.resolve_dominant_meter(results)
    if not dominant_list:
        return ({}, 200)

    first = dominant_list[0]
    meter_name = first.meter_name
    # Enrich with meter data when available (meter_index/meter_roman cover main meters only)
    indices = meter_index(meter_name)
    meter_id = indices[0] if indices else None
    roman = meter_roman(indices[0]) if indices else ""

    out = {
        "meter_name": meter_name,
        "feet": first.feet,
        "is_dominant": True,
    }
    if roman:
        out["meter_roman"] = roman
    if meter_id is not None:
        out["id"] = meter_id
    return out
