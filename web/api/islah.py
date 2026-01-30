# -*- coding: utf-8 -*-
"""
/api/islah: POST poetic input; return progressively detailed scansion by level.

Levels (cumulative):
- syllables: ≥1 word OR ≥2 syllables → code, syllables
- feet:      ≥4 syllables AND ≥1 foot → foot grouping
- meter:     ≥3 feet OR multiple lines → Bahr + deviations
"""

import logging
from typing import Any, Dict, List

from flask import request

from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.utils.meter_align import (
    align_best,
    build_deviations,
    deduce_foot_segments,
    meter_pattern_for_exact_result,
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


def _build_syllables_payload(full_code: str, word_taqti: List[str]) -> Dict[str, Any]:
    """Syllables-level output: code + per-position syllables."""
    word_boundaries = word_boundaries_from_taqti(word_taqti)
    syllables = [{"index": i, "code": c} for i, c in enumerate(full_code)]
    return {
        "full_code": full_code,
        "word_taqti": word_taqti,
        "syllables": syllables,
        "word_boundaries": word_boundaries,
    }


def handle(request):
    """
    Handle /api/islah. POST only. Response is progressively detailed by input:

    - Syllables: ≥1 word OR ≥2 syllables → syllables, code
    - Feet:      ≥4 syllables AND ≥1 foot → feet (foot grouping)
    - Meter:     ≥3 feet OR multiple lines → Bahr + deviations
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
    has_multiple_lines = len(lines) > 1
    line = Lines(line_text)
    scanner = Scansion()
    scanner.add_line(line)

    try:
        # Run scansion (code assignment + prosodic) via exact match path
        scanner.fuzzy = False
        exact = scanner.match_line_to_meters(line, 0)

        # Build full_code and word_taqti from scanned line
        # Use code from scanPath result if available (correct selection from tree traversal),
        # otherwise use first code from each word's code list (not join all alternatives)
        if exact and len(exact) > 0:
            # Use the code from the scanPath result (matches /api/scan behavior)
            word_taqti = exact[0].word_taqti.copy()
            full_code = "".join(word_taqti)
        else:
            # Fallback: use first code from each word (not join all codes in the list)
            word_taqti = [w.code[0] if w.code and len(w.code) > 0 else "" for w in line.words_list]
            full_code = "".join(word_taqti)
        num_syllables = len(full_code)
        num_words = len(line.words_list)

        # Level triggers
        syllables_ok = num_words >= 1 or num_syllables >= 2
        foot_segments = deduce_foot_segments(full_code) if full_code else []
        num_feet = len(foot_segments)
        feet_ok = num_syllables >= 4 and num_feet >= 1
        meter_ok = num_feet >= 3 or has_multiple_lines

        if not syllables_ok:
            return {
                "level": "syllables",
                "explanation": "Insufficient input for scansion (need at least one word or two syllables).",
                "original_line": line_text,
                "full_code": full_code,
                "word_taqti": word_taqti,
                "syllables": [],
                "word_boundaries": word_boundaries_from_taqti(word_taqti),
            }

        level = "meter" if meter_ok else "feet" if feet_ok else "syllables"
        payload: Dict[str, Any] = {
            "level": level,
            "original_line": line_text,
            **_build_syllables_payload(full_code, word_taqti),
        }

        if feet_ok:
            payload["feet"] = foot_segments

        if not meter_ok:
            payload["explanation"] = (
                "Syllables and feet only; add more text (≥3 feet) or multiple lines for Bahr."
            )
            return payload

        # Meter level: exact then fuzzy + align
        if exact:
            payload["conforms_exactly"] = True
            payload["explanation"] = "Line conforms exactly to one or more classical Bahrs."
            payload["bahrs"] = [_bahr_from_exact(so) for so in exact]
            payload["deviations"] = []
            payload["alignment"] = None
            # Include meter pattern for exact match (first matching meter)
            pattern = meter_pattern_for_exact_result(exact[0]) if exact else None
            if pattern is not None:
                payload["meter_pattern_used"] = pattern
            return payload

        fuzzy_results = scanner.scan_line_fuzzy(line, 0)
        if not fuzzy_results:
            payload["conforms_exactly"] = False
            payload["explanation"] = "No exact meter match and no fuzzy match could be inferred."
            payload["bahrs"] = []
            payload["inferred_bahr"] = None
            payload["deviations"] = []
            payload["alignment"] = None
            return payload

        best = min(fuzzy_results, key=lambda so: so.score)
        pattern = meter_pattern_for_fuzzy_result(best)
        payload["conforms_exactly"] = False

        if not pattern:
            payload["explanation"] = "Closest match is a special meter; syllabic alignment not available."
            payload["bahrs"] = []
            payload["inferred_bahr"] = _inferred_bahr_from_fuzzy(best)
            payload["deviations"] = []
            payload["alignment"] = None
            return payload

        distance, edit_ops, leverage = align_best(full_code, pattern)
        payload["explanation"] = (
            f"No exact meter match; inferred closest: {best.meter_name} (edit distance {distance})."
        )
        payload["bahrs"] = []
        payload["inferred_bahr"] = _inferred_bahr_from_fuzzy(best)
        payload["meter_pattern_used"] = pattern
        payload["alignment"] = {
            "distance": distance,
            "edit_ops": edit_ops,
            "leverage": leverage,
        }
        payload["deviations"] = build_deviations(edit_ops)
        return payload
    except Exception:
        logger.exception("Islah error")
        return ({"error": "Error processing line"}, 500)
