# -*- coding: utf-8 -*-
"""
/api/radeefkafiya: POST ghazal text and return radeef/kafiya analysis JSON.

Input:
- JSON: {"text": "..."}
- Form: text=...
- Raw plain text body

Output:
- {"results": {...}}
"""

import logging

from flask import request

from aruuz.rhyme.kafiya import check_kafiya
from aruuz.rhyme.radeef import check_radeef

logger = logging.getLogger(__name__)


def _get_text_from_request(req):
    """
    Extract ghazal text from POST body. Order: JSON -> form -> plain text.
    Returns (text, error) where error is a (dict, status) tuple or None.
    """
    data = req.get_json(force=True, silent=True)
    if isinstance(data, dict) and "text" in data:
        val = data["text"]
        if not isinstance(val, str):
            return None, ({"error": "Field 'text' must be a string"}, 400)
        return (val.strip(), None)

    if req.form and "text" in req.form:
        return (req.form.get("text", "").strip(), None)

    raw = req.get_data(as_text=True)
    return ((raw or "").strip(), None)


def handle(request):
    """
    Handle /api/radeefkafiya. POST only.
    Returns JSON with top-level "results" object.
    """
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    text, err = _get_text_from_request(request)
    if err is not None:
        return err

    if not text:
        return ({"error": "Please enter ghazal text"}, 400)

    try:
        radeef_result = check_radeef(text, mode="strict")
        kafiya_result = check_kafiya(text, radeef_result=radeef_result)
        return {
            "results": {
                "radeef": radeef_result,
                "kafiya": kafiya_result,
            }
        }
    except Exception:
        logger.exception("Radeef-kafiya API error")
        return ({"error": "Error processing ghazal text"}, 500)

