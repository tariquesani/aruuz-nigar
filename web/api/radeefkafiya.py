# -*- coding: utf-8 -*-
"""
/api/radeefkafiya: POST ghazal text and return radeef/kafiya analysis JSON.

Input:
- JSON: {"text": "...", "has_matla": false}
- Form: text=...&has_matla=...
- Raw plain text body

Output:
- {"results": {...}}
"""

import logging

from flask import request

from aruuz.rhyme.kafiya import check_kafiya
from aruuz.rhyme.radeef import check_radeef

logger = logging.getLogger(__name__)


def _parse_has_matla(value) -> bool:
    """Coerce request value to bool; default False when absent."""
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("1", "true", "yes", "on"):
            return True
        if normalized in ("0", "false", "no", "off", ""):
            return False
    return bool(value)


def _get_input_from_request(req):
    """
    Extract ghazal text and has_matla from POST body.
    Order: JSON -> form -> plain text.
    Returns (text, has_matla, error) where error is a (dict, status) tuple or None.
    """
    data = req.get_json(force=True, silent=True)
    if isinstance(data, dict) and "text" in data:
        val = data["text"]
        if not isinstance(val, str):
            return None, False, ({"error": "Field 'text' must be a string"}, 400)
        has_matla = _parse_has_matla(data.get("has_matla"))
        return (val.strip(), has_matla, None)

    if req.form and "text" in req.form:
        has_matla = _parse_has_matla(req.form.get("has_matla"))
        return (req.form.get("text", "").strip(), has_matla, None)

    raw = req.get_data(as_text=True)
    return ((raw or "").strip(), False, None)


def handle(request):
    """
    Handle /api/radeefkafiya. POST only.
    Returns JSON with top-level "results" object.
    """
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    text, has_matla, err = _get_input_from_request(request)
    if err is not None:
        return err

    if not text:
        return ({"error": "Please enter ghazal text"}, 400)

    try:
        radeef_result = check_radeef(text, mode="strict", has_matla=has_matla)
        kafiya_result = check_kafiya(text, radeef_result=radeef_result, has_matla=has_matla)
        return {
            "results": {
                "radeef": radeef_result,
                "kafiya": kafiya_result,
            }
        }
    except Exception:
        logger.exception("Radeef-kafiya API error")
        return ({"error": "Error processing ghazal text"}, 500)
