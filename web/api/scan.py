# -*- coding: utf-8 -*-
"""
/api/scan: POST poetry lines (JSON, form, or plain text), run Scansion.get_scansion, return JSON.
"""

import logging
from flask import request

from aruuz.models import Lines
from aruuz.scansion import Scansion

logger = logging.getLogger(__name__)


def _get_text_from_request(req):
    """
    Extract poetry text from POST body. Order: JSON -> form -> plain text.
    Returns (text, error) where error is a (dict, status) tuple or None.
    """
    # 1. JSON: {"text": "..."}
    data = req.get_json(force=True, silent=True)
    if isinstance(data, dict) and "text" in data:
        val = data["text"]
        if not isinstance(val, str):
            return None, ({"error": "Field 'text' must be a string"}, 400)
        return (val.strip(), None)

    # 2. Form: application/x-www-form-urlencoded or multipart
    if req.form and "text" in req.form:
        return (req.form.get("text", "").strip(), None)

    # 3. Plain text: raw body
    raw = req.get_data(as_text=True)
    return ((raw or "").strip(), None)


def handle(request):
    """
    Handle /api/scan. POST only. Accepts:
    - JSON {"text": "line1\\nline2"}
    - Form POST text=...
    - Plain text body (raw poetry).
    Returns dict or (dict, status).
    """
    if request.method != "POST":
        return ({"error": "Method not allowed"}, 405)

    text, err = _get_text_from_request(request)
    if err is not None:
        return err

    if not text:
        return ({"error": "Please enter at least one line of Urdu poetry"}, 400)

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if not lines:
        return ({"error": "Please enter at least one line of Urdu poetry"}, 400)

    try:
        scanner = Scansion()
        for line_text in lines:
            scanner.add_line(Lines(line_text))
        result = scanner.get_scansion()
        # Rename "results" to "meters" in each line_result for API response
        for line_result in result.get("line_results", []):
            if "results" in line_result:
                line_result["meters"] = line_result.pop("results")
        return result
    except Exception as e:
        logger.exception("Scansion error in /api/scan")
        return ({"error": "Error processing lines"}, 500)
