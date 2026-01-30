#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the same line through exact matching and fuzzy matching, then print both outputs.

For the top 5 fuzzy matches, also prints _align output (edit_ops, leverage).

Usage:
  python scripts/run_exact_vs_fuzzy.py [LINE] [--limit N]
  python scripts/run_exact_vs_fuzzy.py --help
"""

import sys
import os
import io

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from aruuz.utils.logging_config import silence_console_logging, silence_file_logging

silence_console_logging()
silence_file_logging()

from typing import Any, Dict, List, Optional, Tuple

from aruuz.models import Lines, LineScansionResult, LineScansionResultFuzzy
from aruuz.scansion import Scansion
from aruuz.utils.aligner import align
from aruuz.meters import (
    METERS,
    METERS_VARIED,
    RUBAI_METERS,
    RUBAI_METER_NAMES,
    NUM_METERS,
    NUM_VARIED_METERS,
    NUM_RUBAI_METERS,
)


DEFAULT_LINE = "ہزاروں خواہشیں ایسی کہ ہر خواہش پہ دم نکلے"

ALIGN_INTERPRETATION_NOTE = """
  Interpreting align output
  -------------------------
  The aligner compares your line's scansion code (full_code) to the meter pattern
  and reports what already matches (leverage) and what to change (edit_ops).

  LEVERAGE (code ranges), e.g. [(0, 13), (14, 16)]
    • Format: (start, end) = exclusive-end (like Python slices).
    • Meaning: code[0:13] and code[14:16] already match the meter. No edits
      needed there — you can "leverage" (reuse) those stretches.
    • Gaps between ranges = positions where an edit was applied. E.g. a
      "delete code[13]" splits leverage into (0, 13) and (14, 16).
    • Indices are 0-based into full_code; each index = one syllable (- or =).
    • To map to words: full_code = "".join(word_taqti); word boundaries are
      the cumulative lengths of each word's code.

  EDIT_OPS
    • match      — pattern and code agree; part of leverage.
    • substitute — change the code syllable to the pattern syllable (e.g. = -> -).
    • insert     — add a syllable (pattern char) to the line; "before code[k]"
                   = insert before that code position.
    • delete     — remove that code syllable so the line matches the meter.

  Positions (pattern_pos, code_pos) are 0-based. 'x' in code matches - or =;
  the aligner picks one. '~' in pattern matches '-' in code with zero cost.
"""


def _print_align_interpretation_note() -> None:
    print(ALIGN_INTERPRETATION_NOTE)


def _meter_pattern_for_fuzzy(so: LineScansionResultFuzzy) -> Optional[str]:
    """Resolve meter pattern string from a fuzzy result, or None (e.g. special meters)."""
    mid = so.id
    if 0 <= mid < NUM_METERS:
        return METERS[mid]
    if NUM_METERS <= mid < NUM_METERS + NUM_VARIED_METERS:
        return METERS_VARIED[mid - NUM_METERS]
    if mid == -2:
        base = so.meter_name.replace(" (رباعی)", "").strip()
        for idx, name in enumerate(RUBAI_METER_NAMES):
            if name == base:
                return RUBAI_METERS[idx]
        return None
    return None  # special meters (id < -2) or unknown


def _four_variations(meter: str) -> List[str]:
    m = meter.replace("/", "")
    return [
        m.replace("+", ""),
        m.replace("+", "") + "~",
        m.replace("+", "~") + "~",
        m.replace("+", "~"),
    ]


def _align_best(code: str, meter_pattern: str) -> Tuple[int, List[Dict[str, Any]], List[Tuple[int, int]]]:
    """Run align on code vs each of the 4 meter variations; return best (dist, edit_ops, leverage)."""
    best_dist = None
    best_ops: List[Dict[str, Any]] = []
    best_lev: List[Tuple[int, int]] = []
    for v in _four_variations(meter_pattern):
        d, ops, lev = align(v, code)
        if best_dist is None or d < best_dist:
            best_dist = d
            best_ops = ops
            best_lev = lev
    assert best_dist is not None
    return (best_dist, best_ops, best_lev)


def parse_args() -> tuple[str, int]:
    args = sys.argv[1:]
    limit = 20
    line = DEFAULT_LINE
    i = 0
    while i < len(args):
        if args[i] in ("-h", "--help"):
            print("Usage: python run_exact_vs_fuzzy.py [LINE] [--limit N]")
            print("  LINE: Urdu poetry line (default: classic example).")
            print("  --limit N: max results to print per section (default: 20).")
            sys.exit(0)
        if args[i] == "--limit" and i + 1 < len(args):
            limit = int(args[i + 1])
            i += 2
            continue
        line = args[i]
        i += 1
    return (line, limit)


def fmt_result(so: LineScansionResult) -> str:
    code = "".join(so.word_taqti) if so.word_taqti else ""
    words = [w.word for w in so.words] if so.words else []
    return (
        f"  meter_name: {so.meter_name!r}\n"
        f"  id: {so.id}\n"
        f"  feet: {so.feet!r}\n"
        f"  word_taqti: {so.word_taqti}\n"
        f"  full_code: {code!r}\n"
        f"  words: {words}"
    )


def _fmt_align(edit_ops: List[Dict[str, Any]], leverage: List[Tuple[int, int]]) -> str:
    lines = []
    lines.append("  align edit_ops:")
    for o in edit_ops:
        op = o["op"]
        pp, cp = o.get("pattern_pos", -1), o.get("code_pos", -1)
        pc, cc = o.get("pattern_char"), o.get("code_char")
        if op == "match":
            lines.append(f"    match pattern[{pp}]=code[{cp}] {pc!r}={cc!r}")
        elif op == "substitute":
            lines.append(f"    substitute pattern[{pp}]=code[{cp}] {cc!r} -> {pc!r}")
        elif op == "insert":
            lines.append(f"    insert pattern[{pp}] {pc!r} before code[{cp}]")
        else:
            lines.append(f"    delete code[{cp}] {cc!r}")
    lines.append(f"  align leverage (code ranges): {leverage}")
    return "\n".join(lines)


def fmt_fuzzy(
    so: LineScansionResultFuzzy,
    align_info: Optional[Tuple[List[Dict[str, Any]], List[Tuple[int, int]]]] = None,
) -> str:
    code = "".join(so.word_taqti) if so.word_taqti else ""
    words = [w.word for w in so.words] if so.words else []
    out = (
        f"  meter_name: {so.meter_name!r}\n"
        f"  id: {so.id}\n"
        f"  score: {so.score}\n"
        f"  feet: {so.feet!r}\n"
        f"  word_taqti: {so.word_taqti}\n"
        f"  full_code: {code!r}\n"
        f"  words: {words}"
    )
    if align_info is not None:
        out += "\n" + _fmt_align(align_info[0], align_info[1])
    return out


def main() -> None:
    line_text, limit = parse_args()
    line = Lines(line_text)

    scanner = Scansion()
    scanner.add_line(line)

    print("=" * 80)
    print(f"LINE: {line_text}")
    print("=" * 80)

    # --- Exact matching (fuzzy=False) ---
    scanner.fuzzy = False
    exact = scanner.match_line_to_meters(line, 0)

    print("\n--- EXACT MATCHING (fuzzy=False) ---")
    if not exact:
        print("  (no matches)")
    else:
        n = len(exact)
        show = exact[:limit]
        for i, so in enumerate(show):
            print(f"\n  Result {i + 1}:")
            print(fmt_result(so))
        if n > limit:
            print(f"\n  ... and {n - limit} more ({n} total)")

    # --- Fuzzy matching (fuzzy=True) ---
    scanner.fuzzy = True
    fuzzy = scanner.scan_line_fuzzy(line, 0)

    print("\n" + "=" * 80)
    print("--- FUZZY MATCHING (fuzzy=True) ---")
    if not fuzzy:
        print("  (no matches)")
    else:
        # Sort by score ascending (lower = better match); best first
        fuzzy = sorted(fuzzy, key=lambda so: so.score)
        n = len(fuzzy)
        show = fuzzy[:limit]
        top_n = 5
        align_map: Dict[int, Tuple[List[Dict[str, Any]], List[Tuple[int, int]]]] = {}
        for i, so in enumerate(show[:top_n]):
            code = "".join(so.word_taqti) if so.word_taqti else ""
            pat = _meter_pattern_for_fuzzy(so)
            if pat:
                _d, ops, lev = _align_best(code, pat)
                align_map[i] = (ops, lev)
        if align_map:
            _print_align_interpretation_note()
        for i, so in enumerate(show):
            align_info = align_map.get(i)
            print(f"\n  Result {i + 1}:")
            print(fmt_fuzzy(so, align_info))
        if n > limit:
            print(f"\n  ... and {n - limit} more ({n} total)")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
