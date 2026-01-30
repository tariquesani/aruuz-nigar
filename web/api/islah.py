# -*- coding: utf-8 -*-
"""
/api/islah: POST a single poetic line; return full scansion, exact vs fuzzy verdict,
and index-based deviations for guided correction (UI-agnostic).
"""

import logging
from typing import Any, Dict, List

from flask import request

from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.utils.meter_align import (
    align_best,
    build_deviations,
    meter_pattern_for_fuzzy_result,
    word_boundaries_from_taqti,
)

logger = logging.getLogger(__name__)


def _get_text_from_request(req):
    """
    Extract poetry text from POST body. Order: JSON -> form -> plain text.
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


def _bahr_from_exact(so) -> Dict[str, Any]:
    """Build a single bahr dict from a LineScansionResult."""
    full_code = "".join(so.word_taqti) if so.word_taqti else ""
    return {
        "meter_name": so.meter_name,
        "meter_id": so.id,
        "feet": so.feet,
        "full_code": full_code,
    }


def _inferred_bahr_from_fuzzy(so) -> Dict[str, Any]:
    """Build inferred_bahr dict from best LineScansionResultFuzzy."""
    return {
        "meter_name": so.meter_name,
        "meter_id": so.id,
        "feet": so.feet,
        "score": so.score,
    }


def handle(request):
    """
    Handle /api/islah. POST only. Single line (first line used if multiple provided).

    Performs full scansion, checks exact classical Bahr match; if none, uses fuzzy
    matching to infer closest Bahr and align() to pinpoint syllabic deviations.
    Returns structured, index-based data for guided correction (neutral, explainable, UI-agnostic).
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

    line_text = lines[0]
    line = Lines(line_text)
    scanner = Scansion()
    scanner.add_line(line)

    try:
        # Exact match first (fuzzy=False)
        scanner.fuzzy = False
        exact = scanner.match_line_to_meters(line, 0)

        if exact:
            full_code = "".join(exact[0].word_taqti) if exact[0].word_taqti else ""
            bahrs = [_bahr_from_exact(so) for so in exact]
            return {
                "conforms_exactly": True,
                "explanation": "Line conforms exactly to one or more classical Bahrs.",
                "original_line": line_text,
                "full_code": full_code,
                "bahrs": bahrs,
                "deviations": [],
                "alignment": None,
                "word_boundaries": word_boundaries_from_taqti(exact[0].word_taqti),
            }

        # No exact match: fuzzy path
        fuzzy_results = scanner.scan_line_fuzzy(line, 0)
        if not fuzzy_results:
            # Line was already scanned (codes assigned); build full_code from words
            word_codes = ["".join(w.code) for w in line.words_list]
            full_code_fallback = "".join(word_codes)
            return {
                "conforms_exactly": False,
                "explanation": "No exact meter match and no fuzzy match could be inferred.",
                "original_line": line_text,
                "full_code": full_code_fallback,
                "bahrs": [],
                "inferred_bahr": None,
                "deviations": [],
                "alignment": None,
                "word_boundaries": word_boundaries_from_taqti(word_codes),
            }

        # Best fuzzy result (lowest score)
        best = min(fuzzy_results, key=lambda so: so.score)
        full_code = "".join(best.word_taqti) if best.word_taqti else ""
        pattern = meter_pattern_for_fuzzy_result(best)

        if not pattern:
            return {
                "conforms_exactly": False,
                "explanation": "Closest match is a special meter; syllabic alignment not available.",
                "original_line": line_text,
                "full_code": full_code,
                "bahrs": [],
                "inferred_bahr": _inferred_bahr_from_fuzzy(best),
                "deviations": [],
                "alignment": None,
                "word_boundaries": word_boundaries_from_taqti(best.word_taqti),
            }

        distance, edit_ops, leverage = align_best(full_code, pattern)
        deviations = build_deviations(edit_ops)
        word_boundaries = word_boundaries_from_taqti(best.word_taqti)

        return {
            "conforms_exactly": False,
            "explanation": (
                f"No exact meter match; inferred closest: {best.meter_name} "
                f"(edit distance {distance})."
            ),
            "original_line": line_text,
            "full_code": full_code,
            "bahrs": [],
            "inferred_bahr": _inferred_bahr_from_fuzzy(best),
            "meter_pattern_used": pattern,
            "alignment": {
                "distance": distance,
                "edit_ops": edit_ops,
                "leverage": leverage,
            },
            "deviations": deviations,
            "word_boundaries": word_boundaries,
        }
    except Exception as e:
        logger.exception("Islah error")
        return ({"error": "Error processing line"}, 500)
