#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Developer utility to visualize CodeTree for one Urdu line.

Usage:
    python scripts/show_tree.py
    python scripts/show_tree.py "دم اندھیرے میں گھٹ رہا ہے خمارؔ"
"""

import sys
import os
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add parent directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.tree.code_tree import CodeTree

DEFAULT_LINE = "دم اندھیرے میں گھٹ رہا ہے خمارؔ"


def _get_input_line() -> str:
    """Return line from CLI args; fall back to built-in default."""
    if len(sys.argv) > 1:
        return " ".join(sys.argv[1:]).strip()
    return DEFAULT_LINE


text = _get_input_line()


print("=" * 80)
print(f"Visualizing tree for: {text}")
print("=" * 80)
print()

scanner = Scansion()
line_obj = Lines(text)
scanner.add_line(line_obj)

# Process words
for word in line_obj.words_list:
    if not word.code:
        scanner.assign_scansion_to_word(word)

print("WORD CODES ASSIGNED:")
print("-" * 80)
for i, word in enumerate(line_obj.words_list):
    print(f"Word {i} ('{word.word}'): {word.code}")
    if word.taqti_word_graft:
        print(f"  Graft codes: {word.taqti_word_graft}")
print()

# Build tree
tree = CodeTree.build_from_line(
    line_obj,
    error_param=scanner.error_param,
    fuzzy=scanner.fuzzy,
    free_verse=scanner.free_verse
)

print("TREE STRUCTURE:")
print("-" * 80)
print(tree.visualize())
print()

summary = tree.get_summary()
print("SUMMARY:")
print(f"Total nodes: {summary['total_nodes']}")
print(f"Total paths: {summary['total_paths']}")
print(f"Max depth: {summary['max_depth']}")

