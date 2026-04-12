#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Read a ghazal text file and print strict radeef detection JSON.

Usage:
    python scripts/check_radeef.py
    python scripts/check_radeef.py path/to/ghazal.txt
"""

import io
import json
import os
import sys


if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


from aruuz.rhyme.radeef import check_radeef


def _resolve_input_path() -> str:
    """Resolve input file path; default to ghazal.txt in CWD."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    return "ghazal.txt"


def main() -> None:
    path = _resolve_input_path()

    if not os.path.exists(path):
        print(f"Input file not found: {path}", file=sys.stderr)
        print(
            "Usage: python scripts/check_radeef.py [path/to/ghazal.txt]",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    result = check_radeef(text, mode="strict")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

