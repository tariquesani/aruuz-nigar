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
    """
    Send a JSON POST to the Aruuz Nigar API and return the parsed JSON response.
    
    Parameters:
        endpoint (str): Path appended to the configured Aruuz Nigar base URL (e.g., "/api/scan").
        payload (dict): JSON-serializable request body to send.
    
    Returns:
        dict: The parsed JSON response on success. On failure returns a dict with an `"error"` key describing the problem (e.g., connection failure, HTTP error with status code and response text, or other exception message).
    """
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
    Convert an /api/islah response into a compare-ready result describing the line's metrical match status and related metadata.
    
    The returned dictionary always includes at least:
    - `misra`: original line text
    - `full_code`, `word_codes`, `feet_list`: structural code data used for alignment/comparison
    - `result`: one of `"exactly matched"`, `"almost matched"`, or `"no bahr matched"`
    
    Depending on `result`, additional fields are present:
    - For `"exactly matched"`: `bahr`, `bahr_urdu`, `meter_id`, `meter_pattern`, `distance` (0), and `deviations` (empty list).
    - For `"almost matched"`: `bahr`, `bahr_urdu`, `meter_id`, `score`, `meter_pattern`, `distance`, `edit_ops`, and `deviations`.
    - For `"no bahr matched"`: `detail` with a short explanatory message.
    
    Parameters:
        data (dict): Raw JSON-like response from the Aruuz Nigar `/api/islah` endpoint.
    
    Returns:
        dict: A normalized, compare-oriented representation of the analysis suitable for downstream comparison and distance computations.
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
    """
    Format a single /api/scan line_result into the MCP scan response structure.
    
    If no meter candidates are present, the result will be `"no bahr matched"` with a `detail` explaining that no candidates were found. If the selected primary meter has the name `"No meter match found"`, the result will likewise be `"no bahr matched"` with a different explanatory `detail`. Otherwise the result will be `"exactly matched"` and include the matched bahr identifiers.
    
    Parameters:
        line_result (dict): One element from the /api/scan `line_results` list.
    
    Returns:
        dict: Formatted line object including:
            - `misra`: original input line
            - `result`: one of `"exactly matched"` or `"no bahr matched"`
            - `detail`: explanatory text when no match
            - `full_code`, `word_codes`, `syllables`, `syllable_breakdown`
            - `feet_list`
            - `candidate_count`
            - when exactly matched: `bahr` (roman) and `bahr_urdu` (name)
    """
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
    Convert an /api/scan response into the MCP scan output structure.
    
    Returns:
        A single formatted result dict when the input contains one line.
        Otherwise a dict with keys `num_lines` (int) and `results` (list of formatted result dicts).
        If `data` contains an `"error"` key, that dict is returned unchanged.
        If `line_results` is missing or not a list, returns `{"error": "Unexpected /api/scan response: missing line_results list."}`.
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
    """
    Builds a compact per-line detail dictionary used in compare results.
    
    Parameters:
        data (dict): Formatted islah line structure containing keys like `misra`, `result`, `full_code`, `word_codes`, `feet_list`, and optionally `bahr`, `bahr_urdu`, `meter_pattern`, `distance`, `deviations`, `edit_ops`, `detail`.
        label (str): Human-readable label to attach to the detail block (e.g., "reference" or "misra").
    
    Returns:
        dict: Detail dictionary with keys:
            - label (str)
            - misra (str)
            - result (str)
            - full_code (str)
            - word_codes (list)
            - feet_list (list)
            - bahr (str) and bahr_urdu (str) — included if `data` contains `bahr`
            - meter_pattern (str) — included if present
            - distance (numeric) — included if present and not None
            - deviations (list) — included if present
            - edit_ops (list) — included if present
            - detail (str) — included if present
    """
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
    Compute alignment-based distance and alignment details between a source meter code and a target bahr descriptor.
    
    Parameters:
        source_code (str): The encoded meter string for the misra to compare.
        target (dict): A bahr descriptor containing at least `meter_pattern`/`meter_id`/`meter_name` used by the distance API.
    
    Returns:
        dict: On success, a dictionary with keys:
            - `distance` (number|None): Alignment distance between source and target.
            - `meter_pattern` (str): The target's meter pattern.
            - `edit_ops` (list): List of edit operations from the alignment.
            - `deviations` (list): Any deviations reported by the API.
        If the API call failed, returns the original error dictionary returned by the POST helper (contains an `error` key).
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
    """
    Constructs the target descriptor required by the /api/meter/distance endpoint from an islah-derived line structure.
    
    Parameters:
        data (dict): The islah-formatted line dictionary; expected to contain keys `bahr_urdu`, `meter_id`, and `meter_pattern` when available.
    
    Returns:
        dict: A target descriptor with keys:
            - `meter_name` (str): Urdu name of the meter taken from `bahr_urdu` or empty string if missing.
            - `meter_id` (any): Meter identifier taken from `meter_id` (may be None).
            - `meter_pattern` (str): Meter pattern string taken from `meter_pattern` or empty string if missing.
    """
    return {
        "meter_name": data.get("bahr_urdu", ""),
        "meter_id": data.get("meter_id"),
        "meter_pattern": data.get("meter_pattern", ""),
    }


def _format_compare_result(line1_data: dict, line2_data: dict) -> dict:
    """
    Compare two formatted misra analyses and produce a structured comparison verdict and details.
    
    Parameters:
        line1_data (dict): Formatted islah result for the reference misra (compare-oriented structure).
        line2_data (dict): Formatted islah result for the misra under test (compare-oriented structure).
    
    Returns:
        dict: A comparison result containing:
            - result (str): One of "neither misra matched a known bahr", "same bahr", or "different bahr".
            - For "same bahr": `bahr` and `bahr_urdu`.
            - For "different bahr": `reference_bahr`, `reference_bahr_urdu`, `misra_bahr`, `misra_bahr_urdu` (uses "unidentified" or empty string when missing).
            - distance_from_own_bahr (dict, optional): { "reference_distance": <number|null>, "misra_distance": <number|null> } when either input supplies a distance.
            - distance_from_reference_bahr (dict, optional): alignment result when the reference has an identified bahr and the misra has a full code, containing `reference_bahr`, `reference_bahr_urdu`, `meter_pattern`, `misra_code`, `distance`, `edit_ops`, and `deviations`.
            - reference_misra (dict): Per-line detail block for the reference (as produced by _build_line_detail).
            - misra (dict): Per-line detail block for the tested misra (as produced by _build_line_detail).
    """
    if "error" in line1_data:
        return {"error": f"Error scanning first misra: {line1_data['error']}"}
    if "error" in line2_data:
        return {"error": f"Error scanning second misra: {line2_data['error']}"}

    def get_bahr(data):
        """
        Extracts the bahr identifiers from a formatted line result when a bahr match is present.
        
        Parameters:
            data (dict): A formatted result dictionary that may contain the keys
                `"result"`, `"bahr"`, and `"bahr_urdu"`.
        
        Returns:
            tuple: `(bahr, bahr_urdu)` when `data["result"]` is `"exactly matched"` or
            `"almost matched"`, `(None, None)` otherwise.
        """
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
    Scan one or more Urdu misra and produce meter (bahr) analysis.
    
    Accepts a single line or multiple newline-separated lines. Single-line input yields a single formatted result object; multiline input yields a dictionary with `num_lines` and `results` preserving input order.
    
    Parameters:
        misra (str): One or more lines of Urdu poetry (Urdu script or Roman Urdu). Use newlines to separate multiple lines.
    
    Returns:
        dict: For a single line, a formatted result object containing keys such as `result`, `bahr`, `bahr_urdu`, `full_code`, and related analysis fields. For multiple lines, `{'num_lines': <count>, 'results': [<per-line result objects>]}`.
    """
    raw = _post("/api/scan", {"text": misra})
    return _format_scan_api_result(raw)


@mcp.tool()
def compare(misra: str, reference_misra: str) -> dict:
    """
    Compare two Urdu misra and produce a structured verdict with per-line meter analysis.
    
    Returns:
        result (str): Verdict string: one of "same bahr", "different bahr", or "neither misra matched a known bahr".
        reference_misra (dict): Detail block for the reference line containing keys such as `misra`, `misra_code`/`full_code`, `word_codes`, `feet_list`, and, when available, `bahr`, `bahr_urdu`, `meter_pattern`, `distance`, `deviations`, `edit_ops`, or `detail`.
        misra (dict): Detail block for the compared line with the same structure as `reference_misra`.
        distance_from_own_bahr (dict, optional): When available, includes `reference_distance` and/or `misra_distance` showing each line's distance from its own closest matched bahr.
        distance_from_reference_bahr (dict, optional): When computed, contains the reference bahr identifiers and `meter_pattern`, the `misra_code` used for alignment, and alignment results: `distance`, `edit_ops`, and `deviations`.
    """
    line1 = _format_islah_for_compare(_post("/api/islah", {"text": reference_misra}))
    line2 = _format_islah_for_compare(_post("/api/islah", {"text": misra}))
    return _format_compare_result(line1, line2)


@mcp.tool()
def help() -> str:
    """
    List available MCP tools and summarize their behavior.
    
    Provides a concise, human-readable description of the server's tools:
    - scan(misra): Scans one or more Urdu misra (newline-separated). Single-line input returns one formatted result; multiline input returns per-line results.
    - compare(misra, reference_misra): Compares two misra producing a verdict (same/different/unidentified bahr), per-line scansion details (full_code, word_codes, feet, meter_pattern), distance metrics, deviations, and alignment edit operations.
    - help(): Shows this description.
    
    Note: Meter analysis is performed by a locally running Aruuz Nigar service; results are analytical suggestions and may require user judgement.
    
    Returns:
        description (str): A multi-line human-readable help message describing available tools and notes.
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
