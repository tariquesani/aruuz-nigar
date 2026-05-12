"""
Aruuz Nigar MCP Server
A FastMCP wrapper for the Aruuz Nigar poetry meter analysis API.

Usage:
    python aruuz_nigar_mcp.py

Requirements:
    pip install fastmcp httpx

Start servers before opening Claude Desktop:
    python aruuz_nigar.py        # your Aruuz Nigar app
    python aruuz_nigar_mcp.py    # this MCP server

Or use a startup script:
    #!/bin/bash
    python /path/to/aruuz_nigar_app.py &
    python /path/to/aruuz_nigar_mcp.py &

Testing without Claude (recommended before wiring into Claude Desktop):
    fastmcp dev aruuz_nigar_mcp.py
    # opens inspector UI at http://localhost:5173

Claude Desktop config (~/.config/claude/claude_desktop_config.json on Linux,
~/Library/Application Support/Claude/claude_desktop_config.json on macOS):

    {
        "mcpServers": {
            "aruuz-nigar": {
                "url": "http://127.0.0.1:8765/sse"
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


def _format_islah_scan_result(data: dict) -> dict:
    """
    Transform IslahResponse into a clean, LLM-friendly result.
    v0.1 — returns match status and bahr name only.
    """
    if "error" in data:
        return data

    analysis_level = data.get("analysis_level")
    conforms_exactly = data.get("summary", {}).get("conforms_exactly", False)
    original_line = data.get("original_line", "")

    # Did not reach meter level — serious metrical issue
    if analysis_level in ("syllables", "feet"):
        return {
            "misra": original_line,
            "result": "no bahr matched",
            "detail": "Meter could not be identified. The line may have significant metrical issues."
        }

    # Exact match
    meters = data.get("meters", [])
    if conforms_exactly and meters:
        return {
            "misra": original_line,
            "result": "exactly matched",
            "bahr": meters[0].get("meter_roman", ""),
            "bahr_urdu": meters[0].get("meter_name", ""),
        }

    # Inferred / close match
    inferred = data.get("inferred_meter")
    if inferred:
        return {
            "misra": original_line,
            "result": "almost matched",
            "bahr": inferred.get("meter_roman", ""),
            "bahr_urdu": inferred.get("meter_name", ""),
        }

    # Reached meter level but nothing matched
    return {
        "misra": original_line,
        "result": "no bahr matched",
        "detail": "Line was analyzed but did not match or approximate any known bahr."
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


def _format_compare_result(line1_data: dict, line2_data: dict) -> dict:
    """
    Compare meter of two misra.
    v0.1 — reports whether they share the same bahr.
    """
    if "error" in line1_data:
        return {"error": f"Error scanning first misra: {line1_data['error']}"}
    if "error" in line2_data:
        return {"error": f"Error scanning second misra: {line2_data['error']}"}

    def get_bahr(data):
        if data.get("result") == "exactly matched":
            return data.get("bahr"), data.get("bahr_urdu")
        if data.get("result") == "almost matched":
            return data.get("bahr"), data.get("bahr_urdu")
        return None, None

    bahr1, bahr1_urdu = get_bahr(line1_data)
    bahr2, bahr2_urdu = get_bahr(line2_data)

    if not bahr1 and not bahr2:
        return {
            "result": "neither misra matched a known bahr",
            "misra_1_bahr": None,
            "misra_2_bahr": None,
        }

    if bahr1 == bahr2:
        return {
            "result": "same bahr",
            "bahr": bahr1,
            "bahr_urdu": bahr1_urdu,
        }

    return {
        "result": "different bahr",
        "misra_1_bahr": bahr1 or "unidentified",
        "misra_1_bahr_urdu": bahr1_urdu or "",
        "misra_2_bahr": bahr2 or "unidentified",
        "misra_2_bahr_urdu": bahr2_urdu or "",
    }


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
    Compare the meter of two Urdu misra.

    Scans both lines and reports whether they share the same bahr,
    which matters for consistency within a ghazal.

    Args:
        misra: The line to check, in Urdu script or Roman Urdu.
        reference_misra: The reference line to compare against,
                         typically the first misra of the matla.

    Returns:
        A dict with 'result' (same bahr / different bahr / neither matched),
        and bahr names for each line where available.
    """
    line1 = _format_islah_scan_result(_post("/api/islah", {"text": reference_misra}))
    line2 = _format_islah_scan_result(_post("/api/islah", {"text": misra}))
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
        Compares two Urdu misra and reports whether they share the same bahr.
        Useful for checking consistency between lines in a ghazal.
    
    help()
        Shows this description.
    
    Note: All meter analysis is performed by Aruuz Nigar running locally.
    Results should be treated as informed suggestions — use your own
    judgment as the poet.
    """


# --- Entry point -------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8765)
