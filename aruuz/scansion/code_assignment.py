"""
Code Assignment Logic

Main heuristic-based code assignment function.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aruuz.models import Words

from aruuz.utils.araab import remove_araab
from .length_scanners import (
    length_one_scan, length_two_scan, length_three_scan,
    length_four_scan, length_five_scan
)
from .word_analysis import is_vowel_plus_h


def compute_scansion(word: 'Words') -> str:
    """
    Main method that assigns scansion code to a word using heuristics.
    
    This method processes the word, removes special characters,
    splits into syllables if taqti is available, and calls appropriate
    length-based scan methods.
    
    Args:
        word: Words object containing word and taqti information
        
    Returns:
        Scansion code string (e.g., "=-=", "x", etc.)
    """
    # Initialize tracking properties
    word.heuristic_scanner_used = None
    word.heuristic_taqti_used = False
    
    # Create trace list for length_*_scan functions
    trace_steps = []
    
    # Remove araab and special characters
    word1 = remove_araab(word.word)
    word1 = word1.replace("\u06BE", "").replace("\u06BA", "")  # Remove ھ and ں
    
    code = ""
    
    # Handle simple cases first
    if len(word1) == 1:
        word.heuristic_scanner_used = "length_one_scan"
        # SINGLE_SYLLABLE: standalone one-character word
        # Reason: independent syllable, no surrounding context
        code = length_one_scan(word.word, trace=trace_steps)
        word.scan_trace_steps = trace_steps.copy()
        word.scansion_generation_steps.append("APPLIED_LENGTH_ONE_SCAN")
        return code
    elif len(word1) == 2:
        word.heuristic_scanner_used = "length_two_scan"
        code = length_two_scan(word.word, trace=trace_steps)
        word.scan_trace_steps = trace_steps.copy()
        word.scansion_generation_steps.append("APPLIED_LENGTH_TWO_SCAN")
        return code
    
    # For longer words, use taqti if available
    if word.taqti and len(word.taqti) > 0:
        word.heuristic_taqti_used = True
        residue = word.taqti[-1].strip()
        # Remove ھ and ں from taqti
        residue = residue.replace("\u06BE", "").replace("\u06BA", "")
        
        # Split by '+' or space
        delimiters = ['+', ' ']
        sub_strings = []
        current = ""
        for char in residue:
            if char in delimiters:
                if current.strip():
                    sub_strings.append(current.strip())
                current = ""
            else:
                current += char
        if current.strip():
            sub_strings.append(current.strip())
        
        # Append step for taqti segmentation (only if segments exist)
        if sub_strings:
            word.scansion_generation_steps.append(f"USED_TAQTI_BASED_HEURISTIC_SEGMENTATION:count={len(sub_strings)}")
        
        # Process each substring
        for sub_string in sub_strings:
            if not sub_string:
                continue
            
            # Add trace message for taqti substring processing
            trace_steps.append(f"PROCESSING_TAQTI_SUBSTRING: substr={sub_string}")
            
            # Remove ھ and ں for length calculation
            stripped_len = len(remove_araab(sub_string.replace("\u06BE", "").replace("\u06BA", "")))
            
            if stripped_len == 1:
                if word.heuristic_scanner_used is None:
                    word.heuristic_scanner_used = "length_one_scan"
                # SINGLE_SYLLABLE: taqti residue of length 1
                # Reason: fragment produced after syllabic split; treated like standalone mora
                code += length_one_scan(sub_string, trace=trace_steps)
            elif stripped_len == 2:
                if word.heuristic_scanner_used is None:
                    word.heuristic_scanner_used = "length_two_scan"
                # Add trace messages for manual length-2 processing
                trace_steps.append(f"L2S| INPUT_SUBSTRING: substr={sub_string}")
                sub_string_no_aspirate = sub_string.replace("\u06BE", "").replace("\u06BA", "")
                trace_steps.append(f"L2S| AFTER_REMOVING_HAY_AND_NUN: result={sub_string_no_aspirate}")
                stripped = remove_araab(sub_string_no_aspirate)
                # Case 1: alif madd (special long, splittable)
                if stripped and stripped[0] == 'آ':
                    code += "=-"
                    trace_steps.append("L2S| DETECTED_ALIF_MADD_START: return_code=-=")
                # Case 2: inherent long vowel
                elif any(ch in stripped for ch in ['ے', 'و', 'ی']):
                    code += "="
                    trace_steps.append(f"L2S| DETECTED_INHERENT_LONG_VOWEL: return_code==")
                # Case 3: closed short-vowel syllable
                else:
                    code += "x"
                    trace_steps.append("L2S| DETECTED_CLOSED_SHORT_VOWEL_SYLLABLE: return_code=x")
            elif stripped_len == 3:
                if word.heuristic_scanner_used is None:
                    word.heuristic_scanner_used = "length_three_scan"
                code += length_three_scan(sub_string, trace=trace_steps)
            elif stripped_len == 4:
                if word.heuristic_scanner_used is None:
                    word.heuristic_scanner_used = "length_four_scan"
                code += length_four_scan(sub_string, trace=trace_steps)
            elif stripped_len >= 5:
                if word.heuristic_scanner_used is None:
                    word.heuristic_scanner_used = "length_five_scan"
                code += length_five_scan(sub_string, trace=trace_steps)
        
        # Handle word-end flexible syllable
        word_end_rule_applied = False
        if code and (code[-1] == '=' or code[-1] == 'x'):
            if len(word1) > 0 and is_vowel_plus_h(word1[-1]):
                # Check language for Arabic/Persian rules
                if word.language and len(word.language) > 0:
                    is_arabic = any(lang == "عربی" for lang in word.language) and not word.modified
                    is_persian = any(lang == "فارسی" for lang in word.language) and word1[-1] == 'ا' and not word.modified
                    
                    if is_arabic or is_persian:
                        code = code[:-1] + "="
                        word_end_rule_applied = True
                    else:
                        code = code[:-1] + "x"
                        word_end_rule_applied = True
                else:
                    code = code[:-1] + "x"
                    word_end_rule_applied = True
        
        # Append step for word-final rule if it was applied
        if word_end_rule_applied:
            word.scansion_generation_steps.append("APPLIED_WORD_FINAL_VOWEL_H_RULE")
        
        # Append scanner step (once per word) if not already appended for early returns
        if word.heuristic_scanner_used:
            # Check if any scanner step already exists
            scanner_steps_exist = any(
                any(scanner in step for scanner in [
                    "length_one_scan", "length_two_scan", "length_three_scan",
                    "length_four_scan", "length_five_scan"
                ]) for step in word.scansion_generation_steps
            )
            if not scanner_steps_exist:
                word.scansion_generation_steps.append(f"APPLIED_HEURISTIC_SCANNER_USED:scanner={word.heuristic_scanner_used}")
    else:
        # No taqti available - use heuristics based on word length
        if len(word1) == 3:
            word.heuristic_scanner_used = "length_three_scan"
            code = length_three_scan(word.word, trace=trace_steps)
            word.scansion_generation_steps.append("APPLIED_LENGTH_THREE_SCAN")
        elif len(word1) == 4:
            word.heuristic_scanner_used = "length_four_scan"
            code = length_four_scan(word.word, trace=trace_steps)
            word.scansion_generation_steps.append("APPLIED_LENGTH_FOUR_SCAN")
        elif len(word1) >= 5:
            word.heuristic_scanner_used = "length_five_scan"
            code = length_five_scan(word.word, trace=trace_steps)
            word.scansion_generation_steps.append("APPLIED_LENGTH_FIVE_SCAN")
        else:
            code = "-"  # Default fallback
    
    # Copy trace to word before returning
    word.scan_trace_steps = trace_steps.copy()
    return code
