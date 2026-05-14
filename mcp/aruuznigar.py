r"""
Aruuz Nigar MCP Server
A FastMCP wrapper for the Aruuz Nigar poetry meter analysis API.

Usage:
    python .\mcp\aruuznigar.py

Requirements:
    pip install fastmcp httpx

Start servers before opening Claude Desktop:
    python .\app.py        # your Aruuz Nigar app
    python .\mcp\aruuznigar.py    # this MCP server

Testing without Claude (recommended before wiring into Claude Desktop):
    fastmcp dev inspector .\mcp\aruuznigar.py:mcp
    # opens inspector UI at http://localhost:5173

Claude Desktop config (~/.config/claude/claude_desktop_config.json on Linux,
~/Library/Application Support/Claude/claude_desktop_config.json on macOS):

    {
        "mcpServers": {
            "aruuz-nigar": {
                "command": "npx",
                "args": ["mcp-remote", "http://127.0.0.1:8765/sse"]
            }
        }
    }
"""

import httpx
from fastmcp import FastMCP

# --- Configuration -----------------------------------------------------------

ARUUZ_NIGAR_BASE_URL = "http://127.0.0.1:5000"

# --- Server ------------------------------------------------------------------

mcp = FastMCP(
    name="aruuz-nigar",
    instructions="""
    This server provides meter (bahr) analysis for Urdu poetry lines (misra)
    using the Aruuz Nigar engine. Use it during ghazal islah to validate and
    compare meter. Tools available: scan, compare, help.
    """
)

# --- Helpers -----------------------------------------------------------------

def _post(endpoint: str, payload: dict) -> dict:
    """Make a synchronous POST request to Aruuz Nigar."""
    url = f"{ARUUZ_NIGAR_BASE_URL}{endpoint}"
    try:
        response = httpx.post(url, json=payload, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        return {"error": "Cannot reach Aruuz Nigar. Is it running?"}
    except httpx.HTTPStatusError as e:
        return {"error": f"API error {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        return {"error": str(e)}


def _format_islah_for_compare(data: dict) -> dict:
    """
    Transform IslahResponse into a rich, compare-ready result.
    Preserves full_code, meter_pattern, alignment, deviations, and word_codes
    so the compare tool can do structural comparison.
    """
    if "error" in data:
        return data

    analysis_level = data.get("analysis_level")
    conforms_exactly = data.get("summary", {}).get("conforms_exactly", False)
    original_line = data.get("original_line", "")

    base = {
        "misra": original_line,
        "full_code": data.get("full_code", ""),
        "word_codes": data.get("word_codes", []),
        "feet_list": data.get("feet_list", []),
    }

    if analysis_level in ("syllables", "feet"):
        return {
            **base,
            "result": "no bahr matched",
            "detail": "Meter could not be identified. The line may have significant metrical issues.",
        }

    meters = data.get("meters", [])
    if conforms_exactly and meters:
        primary = meters[0]
        return {
            **base,
            "result": "exactly matched",
            "bahr": primary.get("meter_roman", ""),
            "bahr_urdu": primary.get("meter_name", ""),
            "meter_id": primary.get("meter_id"),
            "meter_pattern": data.get("meter_pattern", ""),
            "distance": 0,
            "deviations": [],
        }

    inferred = data.get("inferred_meter")
    if inferred:
        alignment = data.get("alignment") or {}
        return {
            **base,
            "result": "almost matched",
            "bahr": inferred.get("meter_roman", ""),
            "bahr_urdu": inferred.get("meter_name", ""),
            "meter_id": inferred.get("meter_id"),
            "score": inferred.get("score"),
            "meter_pattern": data.get("meter_pattern", ""),
            "distance": alignment.get("distance"),
            "edit_ops": alignment.get("edit_ops", []),
            "deviations": data.get("deviations", []),
        }

    return {
        **base,
        "result": "no bahr matched",
        "detail": "Line was analyzed but did not match or approximate any known bahr.",
    }


def _format_scan_line_result(line_result: dict) -> dict:
    """Transform one /api/scan line_result into MCP scan output shape."""
    original_line = line_result.get("original_line", "")
    meters = line_result.get("meters", []) or []

    if not meters:
        return {
            "misra": original_line,
            "result": "no bahr matched",
            "detail": "No meter candidates found for this line.",
        }

    primary = next((meter for meter in meters if meter.get("is_default")), meters[0])
    full_code = primary.get("full_code", "")
    word_codes = primary.get("word_codes", []) or []
    syllables = [
        {"index": index, "code": code}
        for index, code in enumerate(full_code)
    ]
    syllable_breakdown = []
    syllable_index = 0
    for word_code in word_codes:
        word_syllables = []
        for code in word_code.get("code", ""):
            word_syllables.append({"index": syllable_index, "code": code})
            syllable_index += 1
        syllable_breakdown.append(
            {
                "word": word_code.get("word", ""),
                "code": word_code.get("code", ""),
                "syllables": word_syllables,
            }
        )

    base_result = {
        "misra": original_line,
        "full_code": full_code,
        "syllables": syllables,
        "syllable_breakdown": syllable_breakdown,
        "word_codes": word_codes,
        "feet_list": primary.get("feet_list", []) or [],
        "candidate_count": len(meters),
    }

    if primary.get("meter_name") == "No meter match found":
        return {
            **base_result,
            "result": "no bahr matched",
            "detail": "Line was scanned but did not match any known bahr.",
        }

    return {
        **base_result,
        "result": "exactly matched",
        "bahr": primary.get("meter_roman", ""),
        "bahr_urdu": primary.get("meter_name", ""),
    }


def _format_scan_api_result(data: dict) -> dict:
    """
    Transform /api/scan response into MCP scan output.
    - Single-line input returns a single result object (backward compatible).
    - Multi-line input returns {"results": [...]} preserving line order.
    """
    if "error" in data:
        return data

    line_results = data.get("line_results")
    if not isinstance(line_results, list):
        return {
            "error": "Unexpected /api/scan response: missing line_results list."
        }

    formatted = [_format_scan_line_result(lr) for lr in line_results]
    if len(formatted) == 1:
        return formatted[0]

    return {
        "num_lines": len(formatted),
        "results": formatted,
    }


def _build_line_detail(data: dict, label: str) -> dict:
    """Extract the per-line detail block from a rich islah result."""
    detail = {
        "label": label,
        "misra": data.get("misra", ""),
        "result": data.get("result", ""),
        "full_code": data.get("full_code", ""),
        "word_codes": data.get("word_codes", []),
        "feet_list": data.get("feet_list", []),
    }
    if data.get("bahr"):
        detail["bahr"] = data["bahr"]
        detail["bahr_urdu"] = data.get("bahr_urdu", "")
    if data.get("meter_pattern"):
        detail["meter_pattern"] = data["meter_pattern"]
    if data.get("distance") is not None:
        detail["distance"] = data["distance"]
    if data.get("deviations"):
        detail["deviations"] = data["deviations"]
    if data.get("edit_ops"):
        detail["edit_ops"] = data["edit_ops"]
    if data.get("detail"):
        detail["detail"] = data["detail"]
    return detail


def _meter_distance(source_code: str, target: dict) -> dict:
    """
    Call /api/meter/distance to get proper alignment-based edit distance,
    edit_ops, and deviations for source_code against a target bahr.
    """
    payload = {"source_code": source_code, "target": target}
    raw = _post("/api/meter/distance", payload)
    if "error" in raw:
        return raw
    return {
        "distance": raw.get("distance"),
        "meter_pattern": raw.get("target", {}).get("meter_pattern", ""),
        "edit_ops": raw.get("alignment", {}).get("edit_ops", []),
        "deviations": raw.get("deviations", []),
    }


def _build_target_from_islah(data: dict) -> dict:
    """Build a /api/meter/distance target descriptor from a rich islah result."""
    return {
        "meter_name": data.get("bahr_urdu", ""),
        "meter_id": data.get("meter_id"),
        "meter_pattern": data.get("meter_pattern", ""),
    }


def _format_compare_result(line1_data: dict, line2_data: dict) -> dict:
    """
    Compare meter of two misra with full structural detail.
    Uses /api/meter/distance for proper alignment-based comparison
    against the reference bahr (same engine as the web UI).
    """
    if "error" in line1_data:
        return {"error": f"Error scanning first misra: {line1_data['error']}"}
    if "error" in line2_data:
        return {"error": f"Error scanning second misra: {line2_data['error']}"}

    def get_bahr(data):
        if data.get("result") in ("exactly matched", "almost matched"):
            return data.get("bahr"), data.get("bahr_urdu")
        return None, None

    bahr1, bahr1_urdu = get_bahr(line1_data)
    bahr2, bahr2_urdu = get_bahr(line2_data)

    ref_detail = _build_line_detail(line1_data, "reference_misra")
    misra_detail = _build_line_detail(line2_data, "misra")

    if not bahr1 and not bahr2:
        verdict = "neither misra matched a known bahr"
    elif bahr1 == bahr2:
        verdict = "same bahr"
    else:
        verdict = "different bahr"

    result: dict = {"result": verdict}

    if verdict == "same bahr":
        result["bahr"] = bahr1
        result["bahr_urdu"] = bahr1_urdu

    if verdict == "different bahr":
        result["reference_bahr"] = bahr1 or "unidentified"
        result["reference_bahr_urdu"] = bahr1_urdu or ""
        result["misra_bahr"] = bahr2 or "unidentified"
        result["misra_bahr_urdu"] = bahr2_urdu or ""

    # Distance from own bahr for each line
    ref_dist = line1_data.get("distance")
    misra_dist = line2_data.get("distance")
    if ref_dist is not None or misra_dist is not None:
        result["distance_from_own_bahr"] = {
            "reference_distance": ref_dist,
            "misra_distance": misra_dist,
        }

    # Measure the misra against the *reference* bahr using the alignment engine.
    # This is the key comparison — exactly how the web UI checkbox works.
    misra_code = line2_data.get("full_code", "")
    ref_has_bahr = bahr1 is not None
    if ref_has_bahr and misra_code:
        ref_target = _build_target_from_islah(line1_data)
        dist = _meter_distance(misra_code, ref_target)
        if "error" not in dist:
            result["distance_from_reference_bahr"] = {
                "reference_bahr": bahr1,
                "reference_bahr_urdu": bahr1_urdu or "",
                "meter_pattern": dist["meter_pattern"],
                "misra_code": misra_code,
                "distance": dist["distance"],
                "edit_ops": dist["edit_ops"],
                "deviations": dist["deviations"],
            }

    result["reference_misra"] = ref_detail
    result["misra"] = misra_detail

    return result


# --- Tools -------------------------------------------------------------------

@mcp.tool()
def scan(misra: str) -> dict:
    """
    Scan one or more Urdu misra and return meter (bahr) analysis.

    For single-line input, returns one result object.
    For multiline input (newline-separated), returns a per-line result list.

    Args:
        misra: One or more lines of Urdu poetry in Urdu script or Roman Urdu.
               Separate multiple lines using newlines.

    Returns:
        Single line: {'result', 'bahr', 'bahr_urdu', ...}
        Multiple lines: {'num_lines', 'results': [ ... per-line outputs ... ]}
    """
    raw = _post("/api/scan", {"text": misra})
    return _format_scan_api_result(raw)


@mcp.tool()
def compare(misra: str, reference_misra: str) -> dict:
    """
    Compare the meter of two Urdu misra with full structural detail.

    Scans both lines via the islah engine and returns:
    - Bahr match verdict (same / different / neither matched)
    - Per-line detail: full_code, word_codes, feet_list, meter_pattern,
      distance from bahr, deviations, and edit_ops
    - Positional code comparison showing where the two lines diverge
    - Distance summary showing how far each line is from its closest bahr

    Args:
        misra: The line to check, in Urdu script or Roman Urdu.
        reference_misra: The reference line to compare against,
                         typically the first misra of the matla.

    Returns:
        A dict with 'result' verdict, 'distance_from_own_bahr',
        'distance_from_reference_bahr', and full 'reference_misra' / 'misra'
        detail blocks.
    """
    line1 = _format_islah_for_compare(_post("/api/islah", {"text": reference_misra}))
    line2 = _format_islah_for_compare(_post("/api/islah", {"text": misra}))
    return _format_compare_result(line1, line2)


@mcp.tool()
def help() -> str:
    """
    Describe what this MCP server can do.

    Returns a plain text description of available tools.
    """
    return """
    Aruuz Nigar MCP server provides meter (bahr) analysis for Urdu poetry.
    
    Available tools:
    
    scan(misra)
        Scans one or more Urdu misra (newline-separated text).
        Single-line input returns one result; multiline input returns per-line results.
    
    compare(misra, reference_misra)
        Compares two Urdu misra with full structural detail: bahr match verdict,
        per-line scansion (full_code, word_codes, feet, meter_pattern), distance
        from the closest bahr, deviations, and a positional code diff showing
        exactly where the two lines diverge from each other.
    
    help()
        Shows this description.
    
    Note: All meter analysis is performed by Aruuz Nigar running locally.
    Results should be treated as informed suggestions — use your own
    judgment as the poet.
    """


# --- Entry point -------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8765)
