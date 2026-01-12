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
    # Remove araab and special characters
    word1 = remove_araab(word.word)
    word1 = word1.replace("\u06BE", "").replace("\u06BA", "")  # Remove ھ and ں
    
    code = ""
    
    # Handle simple cases first
    if len(word1) == 1:
        return length_one_scan(word.word)
    elif len(word1) == 2:
        return length_two_scan(word.word)
    
    # For longer words, use taqti if available
    if word.taqti and len(word.taqti) > 0:
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
        
        # Process each substring
        for sub_string in sub_strings:
            if not sub_string:
                continue
            
            # Remove ھ and ں for length calculation
            stripped_len = len(remove_araab(sub_string.replace("\u06BE", "").replace("\u06BA", "")))
            
            if stripped_len == 1:
                code += length_one_scan(sub_string)
            elif stripped_len == 2:
                stripped = remove_araab(sub_string)
                # Case 1: alif madd (special long, splittable)
                if stripped and stripped[0] == 'آ':
                    code += "=-"
                # Case 2: inherent long vowel
                elif any(ch in stripped for ch in ['ے', 'و', 'ی']):
                    code += "="
                # Case 3: closed short-vowel syllable
                else:
                    code += "x"
            elif stripped_len == 3:
                code += length_three_scan(sub_string)
            elif stripped_len == 4:
                code += length_four_scan(sub_string)
            elif stripped_len >= 5:
                code += length_five_scan(sub_string)
        
        # Handle word-end flexible syllable
        if code and (code[-1] == '=' or code[-1] == 'x'):
            if len(word1) > 0 and is_vowel_plus_h(word1[-1]):
                # Check language for Arabic/Persian rules
                if word.language and len(word.language) > 0:
                    is_arabic = any(lang == "عربی" for lang in word.language) and not word.modified
                    is_persian = any(lang == "فارسی" for lang in word.language) and word1[-1] == 'ا' and not word.modified
                    
                    if is_arabic or is_persian:
                        code = code[:-1] + "="
                    else:
                        code = code[:-1] + "x"
                else:
                    code = code[:-1] + "x"
    else:
        # No taqti available - use heuristics based on word length
        if len(word1) == 3:
            code = length_three_scan(word.word)
        elif len(word1) == 4:
            code = length_four_scan(word.word)
        elif len(word1) >= 5:
            code = length_five_scan(word.word)
        else:
            code = "-"  # Default fallback
    
    return code
