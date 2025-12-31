#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to trace meter matching process.
Shows each code sequence being matched and which meters match at each step.
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

from typing import List
from aruuz.models import Lines, scanPath, codeLocation
from aruuz.scansion import Scansion
from aruuz.tree.code_tree import CodeTree
from aruuz.meters import METERS, METERS_VARIED, RUBAI_METERS, NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, USAGE

# Test text (same as test_tree.py)
text = "دم اندھیرے میں گھٹ رہا ہے خمارؔ"

print("=" * 80)
print(f"TRACING METER MATCHING FOR: {text}")
print("=" * 80)
print()

# Initialize scansion
scanner = Scansion()
line_obj = Lines(text)
scanner.add_line(line_obj)

# Process words to assign codes
for word in line_obj.words_list:
    if not word.code:
        scanner.word_code(word)

print("STEP 1: WORD CODES ASSIGNED")
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

print("STEP 2: TREE STRUCTURE")
print("-" * 80)
print(tree.visualize())
print()

# Get all paths from the tree
print("STEP 3: ALL CODE PATHS IN TREE")
print("-" * 80)
all_paths = tree.get_all_paths()
for i, path in enumerate(all_paths, 1):
    # Skip root node
    path_codes = [loc.code for loc in path if loc.code != "root"]
    full_code = ''.join(path_codes)
    print(f"Path {i}: {full_code}")
    print(f"  Locations: ", end="")
    for loc in path:
        if loc.code != "root":
            print(f"Word {loc.word_ref}('{loc.word}')='{loc.code}' ", end="")
    print()
print()

# Now perform meter matching with detailed tracing
print("STEP 4: METER MATCHING PROCESS (DETAILED TRACE)")
print("-" * 80)
print("Tracing traversal step by step...")
print()

# Create a wrapper to trace the matching process
class TracingCodeTree(CodeTree):
    """CodeTree with tracing capabilities."""
    
    def __init__(self, loc):
        super().__init__(loc)
        self.trace_depth = 0
    
    def _traverse_traced(self, scn: scanPath, depth: int = 0) -> List[scanPath]:
        """Traverse with detailed tracing output."""
        indent = "  " * depth
        main_list: List[scanPath] = []
        
        if len(scn.meters) == 0:
            print(f"{indent}⚠️  No meters left to check - backtracking")
            return main_list
        
        if len(self.children) > 0:
            # Build tentative code from current path
            code = ""
            for i in range(len(scn.location)):
                if scn.location[i].code != "root":
                    code += scn.location[i].code
            
            current_node_info = ""
            if self.location.code != "root":
                current_node_info = f" | Node: Word {self.location.word_ref}('{self.location.word}')='{self.location.code}'"
            else:
                current_node_info = " | Node: root"
            
            print(f"{indent}📍 Processing node (depth {depth}){current_node_info}")
            if code:
                print(f"{indent}   Tentative code so far: '{code}' (length: {len(code)})")
            else:
                print(f"{indent}   Tentative code so far: '' (empty, at root)")
            print(f"{indent}   Meters to check: {len(scn.meters)} meter(s)")
            
            # Check each child against meters
            for k in range(len(self.children)):
                child = self.children[k]
                word_code = child.location.code
                tentative_code = code
                indices = list(scn.meters)  # Copy meter indices
                num_indices = len(scn.meters)
                initial_meter_count = len(indices)
                
                print(f"{indent}   └─ Checking child: Word {child.location.word_ref}('{child.location.word}')='{word_code}'")
                print(f"{indent}      Code sequence: '{tentative_code}' + '{word_code}' = '{tentative_code + word_code}'")
                
                # Check each meter index
                removed_meters = []
                for i in range(num_indices):
                    meter_idx = scn.meters[i]
                    
                    if meter_idx < NUM_METERS:
                        # Regular meter
                        if not self._is_match(METERS[meter_idx], tentative_code, word_code):
                            if meter_idx in indices:
                                indices.remove(meter_idx)
                                removed_meters.append(meter_idx)
                    elif meter_idx < NUM_METERS + NUM_VARIED_METERS and meter_idx >= NUM_METERS:
                        # Varied meter
                        if not self._is_match(METERS_VARIED[meter_idx - NUM_METERS], tentative_code, word_code):
                            if meter_idx in indices:
                                indices.remove(meter_idx)
                                removed_meters.append(meter_idx)
                    elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS and meter_idx >= NUM_METERS + NUM_VARIED_METERS:
                        # Rubai meter
                        if not self._is_match(RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS], tentative_code, word_code):
                            if meter_idx in indices:
                                indices.remove(meter_idx)
                                removed_meters.append(meter_idx)
                
                remaining_count = len(indices)
                removed_count = initial_meter_count - remaining_count
                
                if removed_count > 0:
                    print(f"{indent}      ❌ Removed {removed_count} meter(s) that didn't match")
                if remaining_count > 0:
                    print(f"{indent}      ✅ {remaining_count} meter(s) still matching - continuing traversal")
                else:
                    print(f"{indent}      ❌ No meters match - pruning this branch")
                
                # If at least one meter matches, continue traversal
                if remaining_count > 0:
                    scpath = scanPath()
                    scpath.meters = indices
                    for i in range(len(scn.location)):
                        scpath.location.append(scn.location[i])
                    scpath.location.append(child.location)
                    
                    # Recursively traverse child
                    temp = child._traverse_traced(scpath, depth + 1)
                    for i in range(len(temp)):
                        main_list.append(temp[i])
            
            return main_list
        else:
            # Tree leaf - check final code length
            code = ""
            for i in range(len(scn.location)):
                if scn.location[i].code != "root":
                    code += scn.location[i].code
            
            print(f"{indent}🍃 Leaf node reached")
            print(f"{indent}   Final code: '{code}' (length: {len(code)})")
            print(f"{indent}   Meters to validate: {len(scn.meters)} meter(s)")
            
            # Filter meters by code length
            initial_count = len(scn.meters)
            met = self._check_code_length(code, scn.meters)
            final_count = len(met)
            removed_count = initial_count - final_count
            
            if removed_count > 0:
                print(f"{indent}   ❌ Removed {removed_count} meter(s) due to length/pattern mismatch")
            if final_count > 0:
                print(f"{indent}   ✅ {final_count} meter(s) matched!")
                scn.meters = met
                sp = [scn]
                return sp
            else:
                print(f"{indent}   ❌ No meters matched - returning empty")
                return []

# Create a traced version by copying the tree structure
def create_traced_tree(original_tree: CodeTree, depth: int = 0) -> TracingCodeTree:
    """Create a traced version of the tree."""
    traced = TracingCodeTree(original_tree.location)
    traced.error_param = original_tree.error_param
    traced.fuzzy = original_tree.fuzzy
    traced.free_verse = original_tree.free_verse
    
    for child in original_tree.children:
        traced_child = create_traced_tree(child, depth + 1)
        traced.children.append(traced_child)
    
    return traced

# Create traced tree
traced_tree = create_traced_tree(tree)

# Initialize meter list (same logic as find_meter)
indices = []
for i in range(NUM_METERS):
    if USAGE[i] == 1:
        indices.append(i)
for i in range(NUM_METERS):
    if USAGE[i] == 0:
        indices.append(i)
for i in range(NUM_METERS, NUM_METERS + NUM_RUBAI_METERS):
    indices.append(i)

scn = scanPath()
scn.meters = indices
root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
scn.location.append(root_loc)

print(f"🔍 Starting meter matching with {len(indices)} meter(s) to check")
print()

# Perform traced matching
scan_paths = traced_tree._traverse_traced(scn, 0)
print()

print(f"STEP 5: MATCHING RESULTS")
print("-" * 80)
print(f"Total matching paths found: {len(scan_paths)}")
print()

if len(scan_paths) == 0:
    print("❌ NO METERS MATCHED")
    print()
    print("Let's check what code sequences were generated:")
    for i, path in enumerate(all_paths, 1):
        path_codes = [loc.code for loc in path if loc.code != "root"]
        full_code = ''.join(path_codes)
        print(f"  Path {i}: {full_code} (length: {len(full_code)})")
else:
    print("✅ METERS MATCHED:")
    print()
    
    for idx, sp in enumerate(scan_paths, 1):
        # Build code from path
        code_sequence = ""
        word_info = []
        for loc in sp.location:
            if loc.code != "root":
                code_sequence += loc.code
                word_info.append(f"Word {loc.word_ref}('{loc.word}')='{loc.code}'")
        
        print(f"Match {idx}:")
        print(f"  Code sequence: {code_sequence}")
        print(f"  Code length: {len(code_sequence)}")
        print(f"  Path: {' → '.join(word_info)}")
        print(f"  Matched meters: {len(sp.meters)} meter(s)")
        
        # Show meter details
        for meter_idx in sp.meters:
            if meter_idx < NUM_METERS:
                meter_name = f"Regular Meter #{meter_idx}"
                meter_pattern = METERS[meter_idx]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                meter_name = f"Varied Meter #{meter_idx - NUM_METERS}"
                meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                meter_name = f"Rubai Meter #{meter_idx - NUM_METERS - NUM_VARIED_METERS}"
                meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
            else:
                meter_name = f"Special Meter #{meter_idx}"
                meter_pattern = "N/A"
            
            print(f"    - {meter_name}: {meter_pattern}")
        print()

# Additional analysis: Show code sequences that didn't match
print("STEP 6: ANALYSIS")
print("-" * 80)
matched_codes = set()
for sp in scan_paths:
    code = ''.join([loc.code for loc in sp.location if loc.code != "root"])
    matched_codes.add(code)

all_codes = set()
for path in all_paths:
    code = ''.join([loc.code for loc in path if loc.code != "root"])
    all_codes.add(code)

unmatched_codes = all_codes - matched_codes
if unmatched_codes:
    print(f"Code sequences that didn't match any meter ({len(unmatched_codes)}):")
    for code in sorted(unmatched_codes):
        print(f"  - {code} (length: {len(code)})")
else:
    print("All code sequences matched at least one meter!")
print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total code paths in tree: {len(all_paths)}")
print(f"Total unique code sequences: {len(all_codes)}")
print(f"Total matching paths found: {len(scan_paths)}")
print(f"Total unique matched codes: {len(matched_codes)}")
if unmatched_codes:
    print(f"Unmatched code sequences: {len(unmatched_codes)}")
print()

