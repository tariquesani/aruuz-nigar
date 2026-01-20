"""
Deprecated Functions

Functions marked for deprecation but kept for backward compatibility.
"""

import warnings
from typing import List
from aruuz.meters import METERS, METERS_VARIED, RUBAI_METERS, NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS


def is_match(meter: str, tentative_code: str, word_code: str) -> bool:
    """
    Check if a meter pattern matches a code sequence.
    
    .. deprecated:: 
        This function is deprecated. Use the tree-based matching via 
        `CodeTree._is_match()` or `Scansion.match_meters_via_tree()` instead.
        This function is kept for backward compatibility and will be removed
        in a future version.
    
    This function compares a meter pattern with a tentative code (already processed)
    and a word code. It handles 4 variations of the meter pattern:
    1. Original meter with '+' removed
    2. Meter with '+' removed + '-' appended
    3. Meter with '+' replaced by '-' + '-' appended
    4. Meter with '+' replaced by '-'
    
    It also checks caesura positions (word boundaries marked by '+' in meter).
    
    Args:
        meter: Meter pattern string (e.g., "-===/-===/-===/-===")
        tentative_code: Already processed code from previous words
        word_code: Code for the current word
        
    Returns:
        True if any variation of the meter matches the code, False otherwise
    """
    warnings.warn(
        "is_match() is deprecated. Use tree-based matching via CodeTree._is_match() "
        "or Scansion.match_meters_via_tree() instead. This function will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2
    )
    if len(tentative_code) + len(word_code) == 0:
        return False
    
    # Remove '/' from meter
    meter_original = meter.replace("/", "")
    
    # Caesura detection (must check before removing '+')
    # If meter has '+' at position after tentativeCode + wordCode, 
    # wordCode must end with '-'
    if len(meter_original) > len(tentative_code) + len(word_code):
        caesura_pos = len(tentative_code) + len(word_code) - 1
        if caesura_pos >= 0 and caesura_pos < len(meter_original) and meter_original[caesura_pos] == '+':
            if len(word_code) >= 2:
                if word_code[-1] != '-':
                    return False  # Word-boundary caesura violation
            # If word_code length == 1, it's allowed (no check needed)
    
    # Create 4 variations of the meter
    meter2 = meter_original.replace("+", "") + "-"
    meter3 = meter_original.replace("+", "-") + "-"
    meter4 = meter_original.replace("+", "-")
    meter = meter_original.replace("+", "")
    
    # Flags for each variation (True = match, False = no match)
    flag1 = True
    flag2 = True
    flag3 = True
    flag4 = True
    
    code = word_code
    
    # Variation 1: Original meter
    if not (len(meter) < len(tentative_code) + len(word_code)):
        meter_sub = meter[len(tentative_code):]
        i = 0
        while i < len(code):
            if i >= len(meter_sub):
                flag1 = False
                break
            met = meter_sub[i]
            cd = code[i]
            
            # Pattern matching
            if met == '-':
                if cd == '-' or cd == 'x':
                    i += 1
                else:
                    flag1 = False
                    break
            elif met == '=':
                if cd == '=' or cd == 'x':
                    i += 1
                else:
                    flag1 = False
                    break
    else:
        flag1 = False
    
    # Variation 2: meter2 (meter with '+' removed + '-' appended)
    meter = meter2
    i = 0
    if not (len(meter) < len(tentative_code) + len(word_code)):
        meter_sub = meter[len(tentative_code):]
        while i < len(code):
            if i >= len(meter_sub):
                flag2 = False
                break
            met = meter_sub[i]
            cd = code[i]
            
            # Special check for last character
            if i == len(code) - 1:
                if cd != '-':
                    flag2 = False
                    break
            
            # Pattern matching
            if met == '-':
                if cd == '-' or cd == 'x':
                    i += 1
                else:
                    flag2 = False
                    break
            elif met == '=':
                if cd == '=' or cd == 'x':
                    i += 1
                else:
                    flag2 = False
                    break
    else:
        flag2 = False
    
    # Variation 3: meter3 (meter with '+' replaced by '-' + '-' appended)
    meter = meter3
    i = 0
    if not (len(meter) < len(tentative_code) + len(word_code)):
        meter_sub = meter[len(tentative_code):]
        while i < len(code):
            if i >= len(meter_sub):
                flag3 = False
                break
            met = meter_sub[i]
            cd = code[i]
            
            # Special check for last character
            if i == len(code) - 1:
                if cd != '-':
                    flag3 = False
                    break
            
            # Pattern matching
            if met == '-':
                if cd == '-' or cd == 'x':
                    i += 1
                else:
                    flag3 = False
                    break
            elif met == '=':
                if cd == '=' or cd == 'x':
                    i += 1
                else:
                    flag3 = False
                    break
    else:
        flag3 = False
    
    # Variation 4: meter4 (meter with '+' replaced by '-')
    meter = meter4
    i = 0
    if not (len(meter) < len(tentative_code) + len(word_code)):
        meter_sub = meter[len(tentative_code):]
        while i < len(code):
            if i >= len(meter_sub):
                flag4 = False
                break
            met = meter_sub[i]
            cd = code[i]
            
            # Pattern matching
            if met == '-':
                if cd == '-' or cd == 'x':
                    i += 1
                else:
                    flag4 = False
                    break
            elif met == '=':
                if cd == '=' or cd == 'x':
                    i += 1
                else:
                    flag4 = False
                    break
    else:
        flag4 = False
    
    # Return True if any variation matches
    return flag1 or flag2 or flag3 or flag4


def check_code_length(code: str, meter_indices: List[int]) -> List[int]:
    """
    Filter meter indices by checking if code length matches any meter variation.
    
    .. deprecated:: 
        This function is deprecated. Use the tree-based matching via 
        `CodeTree._check_code_length()` or `Scansion.match_meters_via_tree()` instead.
        This function is kept for backward compatibility and will be removed
        in a future version.
    
    This function checks if the given code length matches any of the 4 variations
    of each meter pattern. Meters that don't match any variation are removed.
    
    The 4 variations are:
    1. Original meter with '+' removed
    2. Meter with '+' removed + '-' appended
    3. Meter with '+' replaced by '-' + '-' appended
    4. Meter with '+' replaced by '-'
    
    Args:
        code: Scansion code string (e.g., "=-=")
        meter_indices: List of meter indices to check
        
    Returns:
        List of meter indices that match at least one variation
    """
    warnings.warn(
        "check_code_length() is deprecated. Use tree-based matching via "
        "CodeTree._check_code_length() or Scansion.match_meters_via_tree() instead. "
        "This function will be removed in a future version.",
        DeprecationWarning,
        stacklevel=2
    )
    result = list(meter_indices)  # Copy the list
    
    for meter_idx in meter_indices:
        # Get meter pattern based on index
        if meter_idx < NUM_METERS:
            meter = METERS[meter_idx].replace("/", "")
        elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
            meter = METERS_VARIED[meter_idx - NUM_METERS].replace("/", "")
        elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
            meter = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS].replace("/", "")
        else:
            # Invalid index, skip
            continue
        
        # Create 4 variations
        meter2 = meter.replace("+", "") + "-"
        meter3 = meter.replace("+", "-") + "-"
        meter4 = meter.replace("+", "-")
        meter = meter.replace("+", "")
        
        # Flags for each variation (True = no match, False = match)
        # In C#, flag=True means mismatch, so we invert the logic
        flag1 = True
        flag2 = True
        flag3 = True
        flag4 = True
        
        # Variation 1: Original meter
        if len(meter) == len(code):
            for j in range(len(meter)):
                met = meter[j]
                cd = code[j]
                if met == '-':
                    if cd == '-' or cd == 'x':
                        pass  # Match
                    else:
                        flag1 = True  # Mismatch
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        pass  # Match
                    else:
                        flag1 = True  # Mismatch
                        break
            else:
                # All characters matched
                flag1 = False  # Match found
        else:
            flag1 = True  # Length mismatch
        
        # Variation 2: meter2
        if len(meter2) == len(code):
            for j in range(len(meter2)):
                met = meter2[j]
                cd = code[j]
                if met == '-':
                    if cd == '-' or cd == 'x':
                        pass  # Match
                    else:
                        flag2 = True  # Mismatch
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        pass  # Match
                    else:
                        flag2 = True  # Mismatch
                        break
            else:
                # All characters matched
                flag2 = False  # Match found
        else:
            flag2 = True  # Length mismatch
        
        # Variation 3: meter3
        if len(meter3) == len(code):
            for j in range(len(meter3)):
                met = meter3[j]
                cd = code[j]
                if met == '-':
                    if cd == '-' or cd == 'x':
                        pass  # Match
                    else:
                        flag3 = True  # Mismatch
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        pass  # Match
                    else:
                        flag3 = True  # Mismatch
                        break
            else:
                # All characters matched
                flag3 = False  # Match found
        else:
            flag3 = True  # Length mismatch
        
        # Variation 4: meter4
        if len(meter4) == len(code):
            for j in range(len(meter4)):
                met = meter4[j]
                cd = code[j]
                if met == '-':
                    if cd == '-' or cd == 'x':
                        pass  # Match
                    else:
                        flag4 = True  # Mismatch
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        pass  # Match
                    else:
                        flag4 = True  # Mismatch
                        break
            else:
                # All characters matched
                flag4 = False  # Match found
        else:
            flag4 = True  # Length mismatch
        
        # If all 4 variations fail to match, remove this meter index
        # In C#: if (flag1 && flag2 && flag3 && flag4) list.Remove(i);
        if flag1 and flag2 and flag3 and flag4:
            result.remove(meter_idx)
    
    return result
