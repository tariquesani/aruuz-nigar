#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for tracing meter matching process for sher (couplet) with multiple lines.
Reads lines from a text file and shows how crunch() selects the dominant meter across all lines.
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

from typing import List, Optional
from aruuz.models import Lines, scanPath, codeLocation, scanOutput, Words
from aruuz.scansion import Scansion, is_vowel_plus_h, is_consonant_plus_consonant
from aruuz.tree.code_tree import CodeTree
from aruuz.meters import (
    METERS,
    METERS_VARIED,
    RUBAI_METERS,
    SPECIAL_METER_NAMES,
    NUM_METERS,
    NUM_VARIED_METERS,
    NUM_RUBAI_METERS,
    NUM_SPECIAL_METERS,
    USAGE,
    METER_NAMES,
    METERS_VARIED_NAMES,
    RUBAI_METER_NAMES,
    afail,
    afail_list,
    afail_hindi,
    hindi_feet,
    zamzama_feet,
)
from aruuz.utils.araab import remove_araab

def get_meter_pattern(meter_idx: int) -> Optional[str]:
    """
    Get meter pattern string from meter index.
    
    Args:
        meter_idx: Meter index
        
    Returns:
        Meter pattern string, or None if invalid index
    """
    if meter_idx < NUM_METERS:
        return METERS[meter_idx]
    elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
        return METERS_VARIED[meter_idx - NUM_METERS]
    elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
        return RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
    return None

def get_meter_info_string(meter_name: str, meter_id: int, meter_idx: Optional[int] = None) -> str:
    """
    Create a formatted string with meter name, ID, and pattern.
    
    Args:
        meter_name: Meter name
        meter_id: Meter ID (from scanOutput.id)
        meter_idx: Meter index (if available, for getting pattern)
        
    Returns:
        Formatted string with meter info
    """
    info_parts = [meter_name]
    
    # Add ID
    if meter_id is not None:
        info_parts.append(f"ID: {meter_id}")
    
    # Add pattern if we have meter_idx
    if meter_idx is not None:
        pattern = get_meter_pattern(meter_idx)
        if pattern:
            info_parts.append(f"Pattern: {pattern}")
    
    return " | ".join(info_parts)

# Check command line arguments
if len(sys.argv) < 2:
    print("Usage: python test_sher_matching.py <input_file>")
    print("  The input file should contain one line of Urdu poetry per line")
    print("  Example: python test_sher_matching.py sher.txt")
    sys.exit(1)

input_file = sys.argv[1]

# Check if file exists
if not os.path.isfile(input_file):
    print(f"Error: File '{input_file}' not found")
    sys.exit(1)

# Read lines from file
try:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines_text = [line.strip() for line in f.readlines() if line.strip()]
except Exception as e:
    print(f"Error reading file '{input_file}': {e}")
    sys.exit(1)

if not lines_text:
    print(f"Error: File '{input_file}' is empty or contains no valid lines")
    sys.exit(1)

print("=" * 80)
print(f"TRACING METER MATCHING FOR SHER (COUPLET) - {len(lines_text)} line(s)")
print(f"File: {input_file}")
print("-" * 80)
for i, line in enumerate(lines_text, 1):
    print(f"  Line {i}: {line}")
print("=" * 80)
print()

# Process each line using the same approach as test_meter_matching.py
all_scan_outputs_before_crunch: List[scanOutput] = []
line_objects = []

print("STEP 1: PROCESSING EACH LINE")
print("=" * 80)
print()

for line_idx, line_text in enumerate(lines_text, 1):
    print(f"LINE {line_idx}: {line_text}")
    print("-" * 80)
    
    # Initialize scansion (same as test_meter_matching.py)
    scanner = Scansion()
    line_obj = Lines(line_text)
    scanner.add_line(line_obj)
    line_objects.append(line_obj)
    
    # Process words to assign codes (same as test_meter_matching.py)
    for word in line_obj.words_list:
        if not word.code:
            scanner.assign_scansion_to_word(word)
    
    print("Word codes assigned:")
    for i, word in enumerate(line_obj.words_list):
        print(f"  Word {i} ('{word.word}'): {word.code}")
        if word.taqti_word_graft:
            print(f"    Graft codes: {word.taqti_word_graft}")
    print()
    
    # Step 1.7: Ataf (عطف) Processing - Handle conjunction "و" between words
    print("STEP 1.7: ATAF (عطف) PROCESSING")
    print("-" * 80)
    for i in range(1, len(line_obj.words_list)):
        wrd = line_obj.words_list[i]
        pwrd = line_obj.words_list[i - 1]
        
        if wrd.word == "و":
            print(f"Found 'و' at word {i}, processing with previous word {i-1} ('{pwrd.word}')")
            stripped = remove_araab(pwrd.word)
            length = len(stripped)
            
            if length > 0:
                for k in range(len(pwrd.code)):
                    if is_vowel_plus_h(stripped[length - 1]):
                        # Last char is vowel+h
                        if stripped[length - 1] == 'ا' or stripped[length - 1] == 'ی':
                            # Do nothing as it already in correct form
                            print(f"  Previous word ends with '{stripped[length - 1]}' (ا or ی) - no change needed")
                            pass
                        elif stripped[length - 1] == 'ے' or stripped[length - 1] == 'و':
                            # Modify code and clear current word codes
                            if len(pwrd.code[k]) > 0:
                                last_char = pwrd.code[k][-1]
                                if last_char == "=" or last_char == "x":
                                    pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                    print(f"  Modified previous word code: '{pwrd.code[k]}'")
                                    # Clear all codes in current word ("و")
                                    for j in range(len(wrd.code)):
                                        wrd.code[j] = ""
                                    print(f"  Cleared all codes in 'و': {wrd.code}")
                                elif last_char == "-":
                                    pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                    print(f"  Modified previous word code: '{pwrd.code[k]}'")
                                    # Clear all codes in current word ("و")
                                    for j in range(len(wrd.code)):
                                        wrd.code[j] = ""
                                    print(f"  Cleared all codes in 'و': {wrd.code}")
                        else:
                            # Other vowels: modify code and clear current word codes
                            if len(pwrd.code[k]) > 0:
                                last_char = pwrd.code[k][-1]
                                if last_char == "=" or last_char == "x":
                                    pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                    print(f"  Modified previous word code: '{pwrd.code[k]}'")
                                    # Clear all codes in current word ("و")
                                    for j in range(len(wrd.code)):
                                        wrd.code[j] = ""
                                    print(f"  Cleared all codes in 'و': {wrd.code}")
                                elif last_char == "-":
                                    pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                    print(f"  Modified previous word code: '{pwrd.code[k]}'")
                                    # Clear all codes in current word ("و")
                                    for j in range(len(wrd.code)):
                                        wrd.code[j] = ""
                                    print(f"  Cleared all codes in 'و': {wrd.code}")
                    else:
                        # Last char is consonant
                        if length == 2 and is_consonant_plus_consonant(remove_araab(pwrd.word)):
                            # 2-char consonant+consonant words: set code to "xx" and clear current word codes
                            pwrd.code[k] = "xx"
                            print(f"  Set previous word code to 'xx' (2-char consonant+consonant)")
                            # Clear all codes in current word ("و")
                            for j in range(len(wrd.code)):
                                wrd.code[j] = ""
                            print(f"  Cleared all codes in 'و': {wrd.code}")
                        else:
                            # Otherwise: modify code and clear current word codes
                            if len(pwrd.code[k]) > 0:
                                last_char = pwrd.code[k][-1]
                                if last_char == "=" or last_char == "x":
                                    pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                    print(f"  Modified previous word code: '{pwrd.code[k]}'")
                                    # Clear all codes in current word ("و")
                                    for j in range(len(wrd.code)):
                                        wrd.code[j] = ""
                                    print(f"  Cleared all codes in 'و': {wrd.code}")
                                elif last_char == "-":
                                    pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                    print(f"  Modified previous word code: '{pwrd.code[k]}'")
                                    # Clear all codes in current word ("و")
                                    for j in range(len(wrd.code)):
                                        wrd.code[j] = ""
                                    print(f"  Cleared all codes in 'و': {wrd.code}")
    print()
    
    print("STEP 1.7: WORD CODES AFTER ATAF PROCESSING")
    print("-" * 80)
    for i, word in enumerate(line_obj.words_list):
        print(f"Word {i} ('{word.word}'): {word.code}")
    print()
    
    # Build tree (same as test_meter_matching.py)
    tree = CodeTree.build_from_line(
        line_obj,
        error_param=scanner.error_param,
        fuzzy=scanner.fuzzy,
        free_verse=scanner.free_verse
    )
    
    # Initialize meter list (same as test_meter_matching.py)
    indices = []
    for i in range(NUM_METERS):
        if USAGE[i] == 1:
            indices.append(i)
    for i in range(NUM_METERS):
        if USAGE[i] == 0:
            indices.append(i)
    for i in range(NUM_METERS, NUM_METERS + NUM_RUBAI_METERS):
        indices.append(i)
    # Include special meters (Hindi/Zamzama) via PatternTree (-1 trigger)
    indices.append(-1)
    
    # Use tree.find_meter() directly (same as test_meter_matching.py would do)
    scan_paths = tree.find_meter(indices)
    
    print(f"Found {len(scan_paths)} matching path(s)")
    print()
    
    if len(scan_paths) == 0:
        print("❌ NO METERS MATCHED")
        print()
        
        # Show code sequence even when no matches found
        # Build code sequence from words (use first code variant for each word)
        code_sequence = ""
        word_info = []
        for i, word in enumerate(line_obj.words_list):
            if word.code and len(word.code) > 0 and word.code[0]:
                code_sequence += word.code[0]
                word_info.append(f"Word {i}('{word.word}')='{word.code[0]}'")
        
        if code_sequence:
            print("  Code sequence debug (no matches):")
            print(f"    Code sequence: {code_sequence}")
            print(f"    Code length: {len(code_sequence)}")
            print(f"    Path: {' → '.join(word_info)}")
            print()
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
            
            print(f"  Match {idx}:")
            print(f"    Code sequence: {code_sequence}")
            print(f"    Code length: {len(code_sequence)}")
            print(f"    Path: {' → '.join(word_info)}")
            print(f"    Matched meters: {len(sp.meters)} meter(s)")
            print()
        
        # Convert scan_paths to scanOutput objects (same as test_meter_matching.py STEP 7)
        line_results = []
        for sp in scan_paths:
            if not sp.meters:
                continue  # Skip paths with no matching meters
            
            # Extract words and codes from scanPath location (skip index 0 which is root)
            words_list: List[Words] = []
            word_taqti_list: List[str] = []
            
            for i in range(1, len(sp.location)):
                loc = sp.location[i]
                if loc.word_ref >= 0 and loc.word_ref < len(line_obj.words_list):
                    words_list.append(line_obj.words_list[loc.word_ref])
                    word_taqti_list.append(loc.code)
            
            # Build full code string from word codes
            full_code = "".join(word_taqti_list)
            
            if not full_code:
                continue  # Skip if no code
            
            # Create scanOutput for each matching meter
            for meter_idx in sp.meters:
                so = scanOutput()
                so.original_line = line_obj.original_line
                so.words = words_list.copy()
                so.word_taqti = word_taqti_list.copy()
                so.word_muarrab = [w.word for w in words_list]
                so.num_lines = 1
                
                # Store meter_idx as an attribute for later retrieval (not part of scanOutput model)
                so.meter_idx = meter_idx  # type: ignore
                
                # Determine meter pattern, name, and feet based on meter index
                if meter_idx < NUM_METERS:
                    # Regular meter
                    meter_pattern = METERS[meter_idx]
                    so.meter_name = METER_NAMES[meter_idx]
                    so.feet = afail(meter_pattern)
                    so.feet_list = afail_list(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                    # Varied meter
                    meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
                    so.meter_name = METERS_VARIED_NAMES[meter_idx - NUM_METERS]
                    so.feet = afail(meter_pattern)
                    so.feet_list = afail_list(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                    # Rubai meter
                    meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
                    so.meter_name = RUBAI_METER_NAMES[meter_idx - NUM_METERS - NUM_VARIED_METERS] + " (رباعی)"
                    so.feet = afail(meter_pattern)
                    so.feet_list = afail_list(meter_pattern)
                    so.id = -2
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS + NUM_SPECIAL_METERS:
                    # Special meter (Hindi/Zamzama)
                    special_idx = meter_idx - NUM_METERS - NUM_VARIED_METERS - NUM_RUBAI_METERS
                    if special_idx < len(SPECIAL_METER_NAMES):
                        so.meter_name = SPECIAL_METER_NAMES[special_idx]
                        if special_idx > 7:
                            # Zamzama meters (indices 8-10)
                            so.feet = zamzama_feet(special_idx, full_code)
                        else:
                            # Hindi meters (indices 0-7)
                            so.feet = hindi_feet(special_idx, full_code)
                        if not so.feet:
                            # Fall back to static mapping if dynamic generation fails
                            so.feet = afail_hindi(so.meter_name)
                        so.feet_list = []
                        so.id = -2 - special_idx
                    else:
                        continue  # Skip invalid special meter index
                else:
                    continue  # Skip invalid meter index
                
                line_results.append(so)
        
        all_scan_outputs_before_crunch.extend(line_results)
        
        print(f"Created {len(line_results)} scanOutput object(s) for this line")
        print()
    
    print()

# Show crunch() results across all lines
print("=" * 80)
print("STEP 2: CRUNCH() METHOD - DOMINANT METER SELECTION")
print("=" * 80)
print()

crunched_results = []
if not all_scan_outputs_before_crunch:
    print("❌ No scanOutput objects found (no meter matches)")
else:
    print(f"Found {len(all_scan_outputs_before_crunch)} scanOutput object(s) before crunch()")
    print()
    
    # Show results before crunch (grouped by meter and line)
    print("Results BEFORE crunch() (across all lines):")
    print("-" * 80)
    meter_counts = {}
    line_counts = {}
    for so in all_scan_outputs_before_crunch:
        meter_name = so.meter_name
        if meter_name not in meter_counts:
            meter_counts[meter_name] = []
            line_counts[meter_name] = set()
        meter_counts[meter_name].append(so)
        # Track which lines this meter appears in
        for idx, line_obj in enumerate(line_objects, 1):
            if so.original_line == line_obj.original_line:
                line_counts[meter_name].add(idx)
    
    for meter_name, outputs in meter_counts.items():
        lines_str = f" (lines: {sorted(line_counts[meter_name])})"
        # Get meter pattern and ID from first output (all should have same meter)
        first_so = outputs[0]
        meter_idx = getattr(first_so, 'meter_idx', None)
        meter_pattern = get_meter_pattern(meter_idx) if meter_idx is not None else None
        pattern_str = f" | Pattern: {meter_pattern}" if meter_pattern else ""
        id_str = f" | ID: {first_so.id}" if first_so.id is not None else ""
        print(f"  Meter: {meter_name}{id_str}{pattern_str} - {len(outputs)} result(s){lines_str}")
        for i, so in enumerate(outputs, 1):
            # Find which line this result belongs to
            line_info = ""
            for idx, line_obj in enumerate(line_objects, 1):
                if so.original_line == line_obj.original_line:
                    line_info = f" [Line {idx}]"
                    break
            print(f"    Result {i}{line_info}: feet='{so.feet}', id={so.id}")
    print()
    
    # Show scoring calculation (same logic as crunch())
    print("Scoring calculation (same as crunch()):")
    print("-" * 80)
    meter_names = []
    for item in all_scan_outputs_before_crunch:
        if item.meter_name:
            found = False
            for existing in meter_names:
                if existing == item.meter_name:
                    found = True
                    break
            if not found:
                meter_names.append(item.meter_name)
    
    # Create a scanner for calculate_score
    main_scanner = Scansion()
    scores = [0.0] * len(meter_names)
    for i, meter_name in enumerate(meter_names):
        for item in all_scan_outputs_before_crunch:
            if item.meter_name == meter_name:
                score = main_scanner.calculate_score(meter_name, item.feet)
                scores[i] += score
                # Find which line this score came from
                line_info = ""
                for idx, line_obj in enumerate(line_objects, 1):
                    if item.original_line == line_obj.original_line:
                        line_info = f" [Line {idx}]"
                        break
                # Get meter pattern for display
                meter_idx = getattr(item, 'meter_idx', None)
                meter_pattern = get_meter_pattern(meter_idx) if meter_idx is not None else None
                pattern_str = f" | Pattern: {meter_pattern}" if meter_pattern else ""
                id_str = f" | ID: {item.id}" if item.id is not None else ""
                print(f"  {meter_name}{id_str}{pattern_str}: added score {score} from result with feet '{item.feet}'{line_info} (total so far: {scores[i]})")
    
    print()
    print("Final scores:")
    for i, meter_name in enumerate(meter_names):
        # Find meter info from first matching scanOutput
        meter_info = ""
        for item in all_scan_outputs_before_crunch:
            if item.meter_name == meter_name:
                meter_idx = getattr(item, 'meter_idx', None)
                meter_pattern = get_meter_pattern(meter_idx) if meter_idx is not None else None
                pattern_str = f" | Pattern: {meter_pattern}" if meter_pattern else ""
                id_str = f" | ID: {item.id}" if item.id is not None else ""
                meter_info = f"{id_str}{pattern_str}"
                break
        print(f"  {meter_name}{meter_info}: {scores[i]}")
    print()
    
    # Sort and select dominant meter
    paired = list(zip(scores, meter_names))
    paired.sort(key=lambda x: x[0])  # Sort by score (ascending)
    final_meter = paired[-1][1] if paired else ""
    
    final_score = paired[-1][0] if paired else 0
    # Find the ID and pattern of the dominant meter from the results
    dominant_meter_id = None
    dominant_meter_pattern = None
    for item in all_scan_outputs_before_crunch:
        if item.meter_name == final_meter:
            dominant_meter_id = item.id
            meter_idx = getattr(item, 'meter_idx', None)
            if meter_idx is not None:
                dominant_meter_pattern = get_meter_pattern(meter_idx)
            break
    
    id_str = f" | ID: {dominant_meter_id}" if dominant_meter_id is not None else ""
    pattern_str = f" | Pattern: {dominant_meter_pattern}" if dominant_meter_pattern else ""
    print(f"🏆 Dominant meter selected: {final_meter}{id_str}{pattern_str} (score: {final_score})")
    print()
    
    # Apply crunch() and show results
    print("Applying crunch() method...")
    crunched_results = main_scanner.resolve_dominant_meter(all_scan_outputs_before_crunch)
    print(f"Results AFTER crunch(): {len(crunched_results)} result(s)")
    print("-" * 80)
    
    if crunched_results:
        for i, so in enumerate(crunched_results, 1):
            # Find which line this result belongs to
            line_info = ""
            for idx, line_obj in enumerate(line_objects, 1):
                if so.original_line == line_obj.original_line:
                    line_info = f" [Line {idx}]"
                    break
            
            # Get meter pattern - try from attribute first, then lookup from original scanOutputs
            meter_idx = getattr(so, 'meter_idx', None)
            if meter_idx is None:
                # Try to find meter_idx from original scanOutputs by matching meter_name and original_line
                for orig_so in all_scan_outputs_before_crunch:
                    if orig_so.meter_name == so.meter_name and orig_so.original_line == so.original_line:
                        meter_idx = getattr(orig_so, 'meter_idx', None)
                        if meter_idx is not None:
                            so.meter_idx = meter_idx  # type: ignore
                            break
            
            meter_pattern = get_meter_pattern(meter_idx) if meter_idx is not None else None
            
            print(f"Result {i}{line_info}:")
            print(f"  Meter: {so.meter_name}")
            if meter_pattern:
                print(f"  Pattern: {meter_pattern}")
            print(f"  Feet: {so.feet}")
            print(f"  ID: {so.id}")
            print(f"  is_dominant: {so.is_dominant}")
            print(f"  Original line: {so.original_line}")
            print()
    else:
        print("❌ No results returned from crunch()")
    print()

# Summary
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total lines processed: {len(line_objects)}")
print(f"Total scanOutput objects before crunch(): {len(all_scan_outputs_before_crunch)}")
if all_scan_outputs_before_crunch:
        unique_meters = set(so.meter_name for so in all_scan_outputs_before_crunch if so.meter_name)
        print(f"Unique meters found: {len(unique_meters)}")
        print(f"  Meters: {', '.join(sorted(unique_meters))}")
        if crunched_results:
            print(f"Total scanOutput objects after crunch(): {len(crunched_results)}")
            dominant_so = crunched_results[0] if crunched_results else None
            dominant_meter = dominant_so.meter_name if dominant_so else "None"
            dominant_id = dominant_so.id if dominant_so else None
            dominant_idx = getattr(dominant_so, 'meter_idx', None) if dominant_so else None
            dominant_pattern = get_meter_pattern(dominant_idx) if dominant_idx is not None else None
            
            id_str = f" | ID: {dominant_id}" if dominant_id is not None else ""
            pattern_str = f" | Pattern: {dominant_pattern}" if dominant_pattern else ""
            print(f"Dominant meter: {dominant_meter}{id_str}{pattern_str}")
print()

