#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to visualize CodeTree structure from Urdu poetry lines.

Usage:
    python scripts/visualize_tree.py "your urdu text here"
"""

import sys
import os
import io

# Fix Windows console encoding for Urdu text
if sys.platform == 'win32':
    # Set stdout to UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    else:
        # Fallback for older Python versions
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
    else:
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to path to ensure imports work
# This allows the script to be run from any directory
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from aruuz.models import Lines
    from aruuz.scansion import Scansion
    from aruuz.tree.code_tree import CodeTree
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Script directory: {script_dir}")
    print(f"Parent directory: {parent_dir}")
    print(f"Python path: {sys.path[:3]}")
    sys.exit(1)


def visualize_tree(text: str):
    """
    Build and visualize a CodeTree for the given text.
    
    Args:
        text: Urdu poetry line(s) to visualize
    """
    print("=" * 80)
    print(f"Visualizing tree for: {text}")
    print("=" * 80)
    print()
    
    # Initialize scansion
    scanner = Scansion()
    
    # Process the line
    line_obj = Lines(text)
    scanner.add_line(line_obj)
    
    # IMPORTANT: Process words to assign codes before building tree
    # We need to call scan_line() which does:
    # 1. Assigns codes to words (word_code)
    # 2. Applies contextual adjustments (Al, Izafat, Ataf, Grafting)
    # 3. Builds tree and matches meters
    # We'll call it but only use it to get the processed line, then build our own tree
    # Alternatively, we can manually process - let's use scan_line approach but simpler
    
    # Process words: assign codes
    for word in line_obj.words_list:
        if not word.code:  # Only process if codes not already assigned
            scanner.assign_scansion_to_word(word)
    
    # Show what codes were assigned (for debugging)
    print("WORD CODES ASSIGNED:")
    print("-" * 80)
    for i, word in enumerate(line_obj.words_list):
        print(f"Word {i} ('{word.word}'): {word.code}")
        if word.taqti_word_graft:
            print(f"  Graft codes: {word.taqti_word_graft}")
    print()
    
    # Build the tree (now that words have codes)
    tree = CodeTree.build_from_line(
        line_obj,
        error_param=scanner.error_param,
        fuzzy=scanner.fuzzy,
        free_verse=scanner.free_verse
    )
    
    # Print tree visualization
    print("TREE STRUCTURE:")
    print("-" * 80)
    print(tree.visualize())
    print()
    
    # Print summary
    summary = tree.get_summary()
    print("SUMMARY:")
    print("-" * 80)
    print(f"Total nodes: {summary['total_nodes']}")
    print(f"Total paths: {summary['total_paths']}")
    print(f"Max depth: {summary['max_depth']}")
    print()
    
    # Print word codes
    print("WORD CODES BY WORD REFERENCE:")
    print("-" * 80)
    for word_ref in sorted(summary['word_codes'].keys()):
        codes = summary['word_codes'][word_ref]
        word_text = codes[0]['word'] if codes else "N/A"
        code_list = [c['code'] for c in codes]
        print(f"Word {word_ref} ('{word_text}'): {code_list}")
    print()
    
    # Print all paths
    all_paths = tree.get_all_paths()
    print(f"ALL PATHS ({len(all_paths)} total):")
    print("-" * 80)
    for i, path in enumerate(all_paths, 1):
        # Skip root node
        path_codes = [loc.code for loc in path if loc.code != "root"]
        full_code = ''.join(path_codes)
        print(f"Path {i}: {full_code}")
        
        # Show details
        path_details = []
        for loc in path:
            if loc.code != "root":
                path_details.append(
                    f"  Word {loc.word_ref} ('{loc.word}'): '{loc.code}' (ref: {loc.code_ref})"
                )
        if path_details:
            print("\n".join(path_details))
        print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/visualize_tree.py \"your urdu text here\"")
        print("\nExample:")
        print("  python scripts/visualize_tree.py \"دل کی بات\"")
        sys.exit(1)
    
    text = sys.argv[1]
    visualize_tree(text)


if __name__ == '__main__':
    main()

