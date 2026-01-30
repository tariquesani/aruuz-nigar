"""
Scansion code aligner — DP + backtrack with x/~ rules.

Standalone functions to align a meter pattern to a scansion code string,
returning distance, edit operations, and leverage (match ranges).
Uses same rules as CodeTree._levenshtein_distance: 'x' in code matches
any pattern char except '~'; '~' in pattern matches '-' in code.
"""

from typing import Any, Dict, List, Optional, Tuple


def match_char(p: str, c: str) -> bool:
    """
    True if pattern char p and code char c match under x/~ rules (cost 0).
    - 'x' in code matches any pattern char except '~'
    - '~' in pattern matches '-' in code
    - exact equality also matches
    """
    if (p == c) or (c == "x" and p != "~"):
        return True
    if p == "~" and c == "-":
        return True
    return False


def align(pattern: str, code: str) -> Tuple[int, List[Dict[str, Any]], List[Tuple[int, int]]]:
    """
    Align pattern (meter) to code (line) via DP + backtrack; same x/~ rules as
    CodeTree._levenshtein_distance. Returns (distance, edit_ops, leverage).

    No CodeTree instance required.

    Args:
        pattern: Meter pattern string (e.g. "-===")
        code: Scansion code string (e.g. "-=x=")

    Returns:
        Tuple of:
        - distance: Edit cost (Levenshtein-like)
        - edit_ops: List of {"op": "match"|"insert"|"delete"|"substitute", ...}
        - leverage: List of (code_start, code_end) exclusive-end match ranges

    Example:
        >>> dist, ops, lev = align("-===", "-===")
        >>> dist
        0
        >>> lev
        [(0, 4)]
    """
    m, n = len(pattern), len(code)
    d: List[List[int]] = [[0] * (n + 1) for _ in range(m + 1)]
    bp: List[List[Optional[Tuple[str, str]]]] = [[None] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        d[i][0] = i
    for j in range(n + 1):
        d[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            pc, cc = pattern[i - 1], code[j - 1]
            if match_char(pc, cc):
                d[i][j] = d[i - 1][j - 1]
                bp[i][j] = ("diag", "match")
            else:
                up = d[i - 1][j] + 1
                left = d[i][j - 1] + 1
                diag = d[i - 1][j - 1] + 1
                order = {"diag": 0, "up": 1, "left": 2}
                candidates = [
                    (diag, order["diag"], "diag", "sub"),
                    (up, order["up"], "up", "ins"),
                    (left, order["left"], "left", "del"),
                ]
                candidates.sort(key=lambda x: (x[0], x[1]))
                cost, _, move, kind = candidates[0]
                d[i][j] = cost
                bp[i][j] = (move, kind)

    # Backtrack to build edit_ops (reverse order first)
    rev: List[Dict[str, Any]] = []
    i, j = m, n
    while i > 0 or j > 0:
        if j == 0:
            rev.append({
                "op": "insert",
                "pattern_pos": i - 1,
                "code_pos": 0,
                "pattern_char": pattern[i - 1],
                "code_char": None,
            })
            i -= 1
            continue
        if i == 0:
            rev.append({
                "op": "delete",
                "pattern_pos": -1,
                "code_pos": j - 1,
                "pattern_char": None,
                "code_char": code[j - 1],
            })
            j -= 1
            continue
        move, kind = bp[i][j] or ("diag", "match")
        pc, cc = pattern[i - 1], code[j - 1]
        if move == "diag":
            if kind == "match":
                rev.append({
                    "op": "match",
                    "pattern_pos": i - 1,
                    "code_pos": j - 1,
                    "pattern_char": pc,
                    "code_char": cc,
                })
            else:
                rev.append({
                    "op": "substitute",
                    "pattern_pos": i - 1,
                    "code_pos": j - 1,
                    "pattern_char": pc,
                    "code_char": cc,
                })
            i -= 1
            j -= 1
        elif move == "up":
            rev.append({
                "op": "insert",
                "pattern_pos": i - 1,
                "code_pos": j,
                "pattern_char": pc,
                "code_char": None,
            })
            i -= 1
        else:
            rev.append({
                "op": "delete",
                "pattern_pos": -1,
                "code_pos": j - 1,
                "pattern_char": None,
                "code_char": cc,
            })
            j -= 1

    edit_ops = list(reversed(rev))

    # Leverage: contiguous match segments (code_start, code_end) exclusive-end
    matches = [o for o in edit_ops if o["op"] == "match"]
    leverage: List[Tuple[int, int]] = []
    if matches:
        by_pos = sorted(matches, key=lambda o: (o["pattern_pos"], o["code_pos"]))
        start = by_pos[0]["code_pos"]
        end = by_pos[0]["code_pos"] + 1
        for o in by_pos[1:]:
            cp = o["code_pos"]
            if cp == end:
                end = cp + 1
            else:
                leverage.append((start, end))
                start, end = cp, cp + 1
        leverage.append((start, end))

    return (d[m][n], edit_ops, leverage)
