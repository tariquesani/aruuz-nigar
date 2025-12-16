"""
Core scansion engine for Urdu poetry.

This module contains the main Scansion class that processes
Urdu poetry lines and identifies meters.
"""

from typing import List, Optional
from aruuz.models import Words, Lines, scanOutput
from aruuz.utils.araab import remove_araab, ARABIC_DIACRITICS
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS, 
    METER_NAMES, METERS_VARIED_NAMES, RUBAI_METER_NAMES,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS,
    afail, meter_index
)


def is_vowel_plus_h(char: str) -> bool:
    """
    Check if character is a vowel+h pattern (flexible syllable).
    
    Characters that indicate flexible syllables: ا،ی،ے،و،ہ،ؤ
    
    Args:
        char: Single character to check
        
    Returns:
        True if character is a vowel+h pattern, False otherwise
    """
    return char in ['ا', 'ی', 'ے', 'و', 'ہ', 'ؤ']


def is_muarrab(word: str) -> bool:
    """
    Check if word has diacritical marks (muarrab).
    
    Args:
        word: Word to check
        
    Returns:
        True if word contains any diacritical marks, False otherwise
    """
    for char in word:
        if char in ARABIC_DIACRITICS:
            return True
    return False


def locate_araab(word: str) -> str:
    """
    Extract diacritical marks positions from a word.
    
    Returns a string where each position corresponds to a character,
    with the diacritical mark if present, or space if absent.
    
    Args:
        word: Word with potential diacritical marks
        
    Returns:
        String of diacritical marks aligned with character positions
    """
    loc = ""
    i = 0
    while i < len(word):
        if i < len(word) - 1:
            # Check if next character is a diacritical mark
            if word[i + 1] in ARABIC_DIACRITICS:
                loc += word[i + 1]
                i += 2
            else:
                loc += " "
                i += 1
        else:
            loc += " "
            i += 1
    return loc


def contains_noon(word: str) -> bool:
    """
    Check if word contains noon (ن) character (excluding last position).
    
    Args:
        word: Word to check
        
    Returns:
        True if word contains noon before the last character
    """
    if len(word) > 1:
        for i in range(len(word) - 1):
            if word[i] == 'ن':
                return True
    return False


def noon_ghunna(word: str, code: str) -> str:
    """
    Adjust code for noon ghunna (ن with jazm) patterns.
    
    Args:
        word: Original word
        code: Current scansion code
        
    Returns:
        Adjusted scansion code
    """
    # Remove ھ and ں for processing
    sub_string = word.replace("\u06BE", "").replace("\u06BA", "")
    stripped = remove_araab(sub_string)
    loc = locate_araab(sub_string)
    
    if len(stripped) == 3:
        if stripped[0] == 'آ':
            if stripped[1] == 'ن' and len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazr
                if code == "=--":  # آنت
                    code = "=-"
        elif stripped[1] == 'ن' and len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:
            if code == "=-":
                if stripped[0] == 'ا':  # انگ
                    code = "=-"
                elif is_vowel_plus_h(stripped[0]):  # ہنس
                    code = "="
    elif len(stripped) == 4:
        if stripped[0] == 'آ':
            if stripped[1] == 'ن' and len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:
                if code == "=-=":
                    code = "=="
        elif stripped[1] == 'ن' and len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:
            if code == "==":
                if stripped[0] == 'ا':  # اندر
                    code = "=="
                elif is_vowel_plus_h(stripped[0]):  # ہنسا
                    code = "-="
            # Note: code.Equals("=--") case has no example in C# code
        elif stripped[2] == 'ن' and len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:
            if code == "=--":
                if is_vowel_plus_h(stripped[1]):  # باندھ،اونٹ، ہونٹ
                    code = "=-"
            elif code == "==":
                if is_vowel_plus_h(stripped[1]):  # بانگ
                    if not is_vowel_plus_h(stripped[3]):
                        code = "=-"
    elif len(stripped) == 5:
        if stripped[0] == 'آ':
            if stripped[1] == 'ن' and len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:
                if len(code) > 1 and code[1] == '-':
                    code = code[:1] + code[2:]  # Remove character at position 1
        elif stripped[1] == 'ن' and len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:
            if len(code) > 0 and code[0] == '=':
                # Note: انگیزی case has no code change in C#
                pass
            # Note: code.Equals("=--") case has no example in C# code
        elif stripped[2] == 'ن' and len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:
            if len(code) > 1 and code[0] == '=' and code[1] == '-':
                if is_vowel_plus_h(stripped[1]):
                    code = code[:1] + code[2:]  # Remove character at position 1
        elif stripped[3] == 'ن' and len(loc) > 3 and loc[3] == ARABIC_DIACRITICS[2]:
            if len(code) >= 2 and code[-1] == '-' and code[-2] == '-':
                if is_vowel_plus_h(stripped[2]):
                    if len(code) > 2:
                        if code[-3] == '=':
                            code = code[:-1]  # Remove last character
    
    return code


def length_one_scan(substr: str) -> str:
    """
    Handle 1-character words for scansion.
    
    Args:
        substr: Single character substring
        
    Returns:
        Scansion code: "=" for آ (long), "-" otherwise (short)
    """
    stripped = remove_araab(substr)
    if stripped == "آ":
        return "="
    else:
        return "-"


def length_two_scan(substr: str) -> str:
    """
    Handle 2-character words for scansion.
    
    Two-lettered words ending in ا،ی،ے،و،ہ are treated as flexible.
    
    Args:
        substr: Two-character substring
        
    Returns:
        Scansion code: "=-" if starts with آ, "x" if ends with vowel+h, "=" otherwise
    """
    # Remove ھ and ں for scansion purposes
    sub_string = substr.replace("\u06BE", "").replace("\u06BA", "")
    stripped = remove_araab(sub_string)
    
    code = "="
    if substr[0] == '\u0622':  # آ
        code = "=-"
    elif len(stripped) > 0 and is_vowel_plus_h(stripped[-1]):
        code = "x"
    
    return code


def length_three_scan(substr: str) -> str:
    """
    Handle 3-character words for scansion.
    
    Args:
        substr: Three-character substring
        
    Returns:
        Scansion code based on character patterns and diacritics
    """
    code = ""
    # Remove ھ and ں for scansion purposes
    sub_string = substr.replace("\u06BE", "").replace("\u06BA", "")
    stripped = remove_araab(sub_string)
    
    if len(stripped) == 1:
        if stripped[0] == 'آ':
            return "-"
        else:
            return "="
    elif len(stripped) == 2:
        return length_two_scan(substr)
    
    if is_muarrab(sub_string):
        loc = locate_araab(sub_string)
        
        if len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazm
            if stripped[0] == 'آ':
                code = "=--"
            else:
                code = "=-"
        elif len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                               loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                               loc[1] == ARABIC_DIACRITICS[9]):  # paish
            code = "-="
        elif len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[0]:  # shadd
            code = "=="
        elif len(stripped) > 2 and stripped[2] == 'ا':
            code = "-="
        elif len(stripped) > 2 and stripped[2] in ['ا', 'ی', 'ے', 'و', 'ہ']:  # vowels at end
            if stripped[1] == 'ا':
                code = "=-"
            else:
                code = "-="
        elif (len(stripped) > 1 and stripped[1] in ['ا', 'ی', 'ے', 'و']) or (len(stripped) > 2 and stripped[2] == 'ہ'):  # vowels at center
            code = "=-"
        else:  # default case
            code = "=-"
    else:
        if stripped[0] == 'آ':
            code = "=="
        elif len(stripped) > 1 and stripped[1] == 'ا':  # Alif at centre
            code = "=-"
        elif len(stripped) > 2 and stripped[2] == 'ا':
            code = "-="
        elif len(stripped) > 1 and stripped[1] in ['ی', 'ے', 'و', 'ہ']:  # vowels + h at centre
            if len(stripped) > 2 and stripped[2] == 'ہ':
                code = "=-"
            elif len(stripped) > 2 and stripped[2] in ['ی', 'ے', 'و']:  # vowels + h at end
                code = "-="
            else:
                code = "=-"
        elif len(stripped) > 2 and stripped[2] in ['ی', 'ے', 'و', 'ہ']:  # vowels + h at end
            code = "-="
        elif len(stripped) > 0 and is_vowel_plus_h(stripped[0]):
            code = "-="
        else:
            code = "-="
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(stripped):
        code = noon_ghunna(substr, code)
    
    return code


def length_four_scan(substr: str) -> str:
    """
    Handle 4-character words for scansion.
    
    Args:
        substr: Four-character substring
        
    Returns:
        Scansion code based on character patterns
    """
    code = ""
    # Remove ھ and ں for scansion purposes
    sub_string = substr.replace("\u06BE", "").replace("\u06BA", "")
    stripped = remove_araab(sub_string)
    
    if len(stripped) == 1:
        code = length_one_scan(sub_string)
    elif len(stripped) == 2:
        code = length_two_scan(sub_string)
    elif len(stripped) == 3:
        code = length_three_scan(sub_string)
    else:
        if stripped[0] == 'آ':
            # Remove first character and scan the rest
            remaining = sub_string[1:] if len(sub_string) > 1 else ""
            code = "=" + length_three_scan(remaining)
        elif is_muarrab(sub_string):
            loc = locate_araab(sub_string)
            if len(stripped) > 1 and stripped[1] == 'ا':
                if len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                    code = "=--"
                else:
                    code = "=="
            elif len(stripped) > 2 and stripped[2] == 'ا':
                code = "-=-"
            else:
                if len(stripped) > 1 and stripped[1] == 'و':
                    if len(stripped) > 3 and stripped[3] == 'ت' and len(loc) > 3 and loc[3] == ARABIC_DIACRITICS[2]:  # jazm
                        code = "=-"
                    else:
                        if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                            loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            loc[1] == ARABIC_DIACRITICS[9]):  # paish
                            code = "-=-"
                        else:
                            if len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "=--"
                            else:
                                code = "=="
                elif len(stripped) > 1 and stripped[1] == 'ی':
                    if len(stripped) > 3 and stripped[3] == 'ت' and len(loc) > 3 and loc[3] == ARABIC_DIACRITICS[2]:  # jazm
                        code = "=-"
                    elif len(loc) > 0 and (loc[0] == ARABIC_DIACRITICS[1] or  # zer
                                           loc[0] == ARABIC_DIACRITICS[8] or  # zabar
                                           loc[0] == ARABIC_DIACRITICS[9]):  # paish
                        if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                            loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            loc[1] == ARABIC_DIACRITICS[9]):  # paish
                            code = "-=-"
                        else:
                            if len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "=--"
                            else:
                                code = "=="
                    else:
                        code = "=="
                else:
                    if len(loc) > 0 and (loc[0] == ARABIC_DIACRITICS[1] or  # zer
                                        loc[0] == ARABIC_DIACRITICS[8] or  # zabar
                                        loc[0] == ARABIC_DIACRITICS[9]):  # paish
                        if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                            loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            loc[1] == ARABIC_DIACRITICS[9]):  # paish
                            if len(stripped) > 2 and is_vowel_plus_h(stripped[2]):
                                code = "-=-"
                            elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "-=-"
                            else:
                                code = "--="
                        elif len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "=="
                        elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=-"
                        else:
                            if len(stripped) > 3 and (stripped[3] == 'ا' or stripped[3] == 'ی'):
                                code = "--="
                            else:
                                code = "-=-"
                    elif len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazr
                        if len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "=="
                        else:
                            code = "=--"
                    elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "-=-"
                    elif len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                          loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                          loc[2] == ARABIC_DIACRITICS[9]):  # paish
                        code = "=="
                    elif len(stripped) > 2 and is_vowel_plus_h(stripped[2]):
                        code = "-=-"
                    else:
                        code = "=="
        elif len(stripped) > 2 and is_vowel_plus_h(remove_araab(sub_string)[2]):
            stripped_sub = remove_araab(sub_string)
            if len(stripped_sub) > 3 and stripped_sub[3] == 'ا':
                code = "=="
            elif len(stripped_sub) > 1 and is_vowel_plus_h(stripped_sub[1]):
                code = "=="
            else:
                code = "-=-"
        else:  # default
            code = "=="
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(stripped):
        code = noon_ghunna(substr, code)
    
    return code


def length_five_scan(substr: str) -> str:
    """
    Handle 5+ character words for scansion.
    
    Args:
        substr: Five or more character substring
        
    Returns:
        Scansion code based on character patterns
    """
    code = ""
    # Remove ھ and ں for scansion purposes
    sub_string = substr.replace("\u06BE", "").replace("\u06BA", "")
    stripped = remove_araab(sub_string)
    
    # --- FIX: aspirated + ی should force short medial vowel (e.g. اندھیرے) ---
    if 'ھ' in substr:
        for i in range(len(substr) - 2):
            if substr[i+1] == 'ھ' and substr[i+2] == 'ی':
                return "-=="    
    if len(stripped) == 3:
        code = length_three_scan(substr)
    elif len(stripped) == 4:
        code = length_four_scan(substr)
    else:
        if stripped[0] == 'آ':
            # Remove first 2 characters (آ + next) and scan the rest
            remaining = sub_string[2:] if len(sub_string) > 2 else ""
            code = "=" + length_four_scan(remaining)
        elif is_muarrab(sub_string):
            loc = locate_araab(sub_string)
            if len(stripped) > 1 and (stripped[1] == 'ا' or stripped[2] == 'ا' or stripped[3] == 'ا'):  # check alif at position 2,3,4
                # Position 3 Alif
                if len(stripped) > 2 and stripped[2] == 'ا':
                    code = "-=="
                # Position 2 Alif
                elif len(stripped) > 1 and stripped[1] == 'ا':
                    if len(loc) > 0 and is_muarrab(loc[0]):
                        if len(loc) > 1 and is_muarrab(loc[1]):
                            code = "=" + length_three_scan(sub_string[3:] if len(sub_string) > 3 else "")
                        else:
                            code = "=" + length_three_scan(sub_string[4:] if len(sub_string) > 4 else "")
                    else:
                        if len(loc) > 1 and is_muarrab(loc[1]):
                            code = "=" + length_three_scan(sub_string[2:] if len(sub_string) > 2 else "")
                        else:
                            code = "=" + length_three_scan(sub_string[3:] if len(sub_string) > 3 else "")
                # Position 4 Alif
                else:
                    code = "==-"
                    if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                         loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         loc[1] == ARABIC_DIACRITICS[9]):  # paish
                        code = "--=-"
                    elif len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "--=-"
                    elif len(stripped) > 0 and stripped[0] == 'ب':
                        if len(stripped) > 1 and is_vowel_plus_h(stripped[1]):
                            code = "==-"
                        elif len(stripped) > 1 and stripped[1] == 'ر':
                            code = "==-"
                        elif len(stripped) > 1 and stripped[1] == 'ن':
                            code = "==-"
                        elif len(stripped) > 1 and stripped[1] == 'غ':
                            code = "==-"
                        else:
                            code = "--=-"
            else:
                if len(stripped) > 1 and (stripped[1] == 'و' or stripped[2] == 'و' or stripped[3] == 'و' or
                                         stripped[1] == 'ی' or stripped[2] == 'ی' or stripped[3] == 'ی'):
                    if len(stripped) > 1 and (stripped[1] == 'و' or stripped[1] == 'ی'):
                        if len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazr
                            if len(loc) > 0 and is_muarrab(loc[0]):
                                if len(loc) > 1 and is_muarrab(loc[1]):
                                    code = "=" + length_three_scan(sub_string[5:] if len(sub_string) > 5 else "")
                                else:
                                    code = "=" + length_three_scan(sub_string[4:] if len(sub_string) > 4 else "")
                            else:
                                if len(loc) > 1 and is_muarrab(loc[1]):
                                    code = "=" + length_three_scan(sub_string[3:] if len(sub_string) > 3 else "")
                                else:
                                    code = "=" + length_three_scan(sub_string[4:] if len(sub_string) > 4 else "")
                        elif len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                               loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                               loc[1] == ARABIC_DIACRITICS[9]):  # paish
                            if len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                                 loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                                 loc[2] == ARABIC_DIACRITICS[9]):  # paish
                                code = "--=-"
                            else:
                                code = "-=="
                        else:
                            if len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                                 loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                                 loc[2] == ARABIC_DIACRITICS[9]):  # paish
                                if len(loc) > 3 and (loc[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     loc[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     loc[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "=-="
                                elif len(loc) > 3 and loc[3] == ARABIC_DIACRITICS[2]:  # jazr
                                    code = "==-"
                                else:
                                    code = "==-"
                            elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                                if len(loc) > 3 and (loc[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     loc[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     loc[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "=-="
                                elif len(loc) > 3 and loc[3] == ARABIC_DIACRITICS[2]:  # jazr
                                    code = "=---"
                                else:
                                    if len(loc) > 2 and is_muarrab(loc[2]):
                                        code = "=" + length_three_scan(sub_string[4:] if len(sub_string) > 4 else "")
                                    else:
                                        code = "=" + length_three_scan(sub_string[3:] if len(sub_string) > 3 else "")
                            else:
                                code = "=" + length_three_scan(sub_string[2:] if len(sub_string) > 2 else "")
                    elif len(stripped) > 2 and (stripped[2] == 'و' or stripped[2] == 'ی'):
                        if len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                            loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            loc[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                                loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                loc[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(loc) > 3 and (loc[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     loc[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     loc[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "-----"  # highly unlikely
                                else:
                                    code = "--=-"
                        elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "-=="
                    elif len(stripped) > 3 and (stripped[3] == 'و' or stripped[3] == 'ی'):
                        if len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                            loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            loc[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                                loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                loc[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(loc) > 3 and (loc[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     loc[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     loc[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "---="  # highly unlikely
                                else:
                                    code = "--=-"
                        elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "==-"
                    else:
                        if len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                             loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                             loc[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                                loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                loc[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(loc) > 3 and (loc[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     loc[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     loc[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "-----"  # highly unlikely
                                else:
                                    code = "--=-"
                        elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "==-"
                else:
                    if len(loc) > 1 and (loc[1] == ARABIC_DIACRITICS[1] or  # zer
                                         loc[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         loc[1] == ARABIC_DIACRITICS[9]):  # paish
                        if len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                            loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            loc[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(stripped) > 4 and stripped[4] == 'ا':
                                code = "---="
                            else:
                                code = "--=-"
                        elif len(loc) > 2 and loc[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "-=="
                    elif len(loc) > 1 and loc[1] == ARABIC_DIACRITICS[2]:  # jazr
                        if len(loc) > 0 and is_muarrab(loc[0]):
                            code = "=" + length_three_scan(sub_string[4:] if len(sub_string) > 4 else "")
                        else:
                            code = "=" + length_three_scan(sub_string[3:] if len(sub_string) > 3 else "")
                    elif len(loc) > 2 and (loc[2] == ARABIC_DIACRITICS[1] or  # zer
                                          loc[2] == ARABIC_DIACRITICS[8] or  # zabar
                                          loc[2] == ARABIC_DIACRITICS[9]):  # paish
                        code = "=-="
                    # else: empty code (no change)
        elif len(stripped) > 1 and (stripped[1] == 'ا' or stripped[2] == 'ا' or stripped[3] == 'ا'):  # check alif at position 2,3,4
            # Position 3 Alif
            if len(stripped) > 2 and stripped[2] == 'ا':
                code = "-=="
            # Position 2 Alif
            elif len(stripped) > 1 and stripped[1] == 'ا':
                if len(stripped) > 3 and stripped[3] == 'ا':
                    code = "==-"
                else:
                    if len(stripped) > 3 and is_vowel_plus_h(stripped[3]):
                        if len(stripped) > 4 and is_vowel_plus_h(stripped[4]):
                            code = "=-="
                        else:
                            code = "==-"
                    elif len(stripped) > 4 and is_vowel_plus_h(stripped[4]):
                        code = "=-="
                    else:
                        code = "==-"
            # Position 4 Alif
            else:
                code = "==-"
                if len(stripped) > 0 and stripped[0] == 'ب':
                    if len(stripped) > 1 and is_vowel_plus_h(stripped[1]):
                        code = "==-"
                    elif len(stripped) > 1 and stripped[1] == 'ر':
                        code = "==-"
                    elif len(stripped) > 1 and stripped[1] == 'ن':
                        code = "==-"
                    elif len(stripped) > 1 and stripped[1] == 'غ':
                        code = "==-"
                    else:
                        code = "--=-"
        elif len(stripped) > 1 and (is_vowel_plus_h(stripped[1]) or is_vowel_plus_h(stripped[2]) or is_vowel_plus_h(stripped[3])):  # check vowels at position 2,3,4
            # Position 3 Vowel
            if len(stripped) > 2 and is_vowel_plus_h(stripped[2]):
                code = "-=="
                if len(stripped) > 3 and is_vowel_plus_h(stripped[3]):
                    code = "-=="
            # Position 2 Vowel
            elif len(stripped) > 1 and is_vowel_plus_h(stripped[1]):
                if len(stripped) > 3 and is_vowel_plus_h(stripped[3]):
                    code = "==-"
                else:
                    if len(stripped) > 3 and is_vowel_plus_h(stripped[3]):
                        if len(stripped) > 4 and is_vowel_plus_h(stripped[4]):
                            code = "=-="
                        else:
                            code = "==-"
                    elif len(stripped) > 4 and is_vowel_plus_h(stripped[4]):
                        code = "=-="
                    else:
                        code = "==-"
            # Position 4 Vowel
            else:
                code = "==-"
                if len(stripped) > 0 and stripped[0] == 'ب':
                    if len(stripped) > 1 and is_vowel_plus_h(stripped[1]):
                        code = "==-"
                    elif len(stripped) > 1 and stripped[1] == 'ر':
                        code = "==-"
                    elif len(stripped) > 1 and stripped[1] == 'ن':
                        code = "==-"
                    elif len(stripped) > 1 and stripped[1] == 'غ':
                        code = "==-"
                    else:
                        code = "--=-"
                if len(stripped) > 4 and stripped[4] == 'ت' and len(stripped) > 3 and stripped[3] == 'ی':
                    code = code[:-1] + "="
        else:  # consonants
            code = "==-"
            if len(stripped) > 0 and stripped[0] == 'ب':
                if len(stripped) > 1 and is_vowel_plus_h(stripped[1]):
                    code = "==-"
                elif len(stripped) > 1 and stripped[1] == 'ر':
                    code = "==-"
                elif len(stripped) > 1 and stripped[1] == 'ن':
                    code = "==-"
                elif len(stripped) > 1 and stripped[1] == 'غ':
                    code = "==-"
                else:
                    code = "--=-"
            if len(stripped) > 0 and (stripped[0] == 'ت' or stripped[0] == 'ش'):
                code = "-=="
            if len(stripped) > 4 and stripped[4] == 'ت' and len(stripped) > 3 and stripped[3] == 'ی':
                code = code[:-1] + "="
            if len(stripped) > 4 and stripped[4] == 'ا':
                code = "-=="
            elif len(stripped) > 4 and is_vowel_plus_h(stripped[4]):
                code = "=-="
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(stripped):
        code = noon_ghunna(substr, code)
    
    return code


def assign_code(word: Words) -> str:
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
                if stripped and stripped[0] == 'آ':
                    code += "=-"
                else:
                    code += "="
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


def is_match(meter: str, tentative_code: str, word_code: str) -> bool:
    """
    Check if a meter pattern matches a code sequence.
    
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


class Scansion:
    """
    Main scansion engine for Urdu poetry.
    
    This class processes lines of Urdu poetry, assigns scansion codes to words,
    and matches them against meter patterns.
    """
    
    def __init__(self):
        """Initialize a new Scansion instance."""
        self.lst_lines: List[Lines] = []
        self.num_lines: int = 0
        self.is_checked: bool = False
        self.free_verse: bool = False
        self.fuzzy: bool = False
        self.error_param: int = 8
        self.meter: Optional[List[int]] = None
    
    def add_line(self, line: Lines) -> None:
        """
        Add a line to the scansion engine.
        
        Args:
            line: Lines object containing the poetry line
        """
        self.lst_lines.append(line)
        self.num_lines += 1
    
    def word_code(self, word: Words) -> Words:
        """
        Assign scansion code to a word using heuristics.
        
        This method uses the assign_code function to determine the scansion
        code for a word based on its length and characteristics.
        
        Args:
            word: Words object to assign code to
            
        Returns:
            Words object with code assigned
        """
        # If word already has codes, return as is
        if len(word.code) > 0:
            return word
        
        # Use heuristics to assign code
        code = assign_code(word)
        
        # Store code in word
        word.code = [code]
        
        return word
    
    def scan_line(self, line: Lines, line_index: int) -> List[scanOutput]:
        """
        Process a single line and return possible scan outputs.
        
        This method:
        1. Assigns codes to all words in the line
        2. Builds a complete code string
        3. Matches against all meters
        4. Creates scanOutput objects for matches
        
        Args:
            line: Lines object to scan
            line_index: Index of the line (for reference)
            
        Returns:
            List of scanOutput objects representing possible meter matches
        """
        results: List[scanOutput] = []
        
        # Step 1: Assign codes to all words
        word_codes: List[str] = []
        for word in line.words_list:
            word = self.word_code(word)
            if len(word.code) > 0:
                word_codes.append(word.code[0])
            else:
                # If no code assigned, skip this word or use default
                word_codes.append("-")
        
        # Step 2: Build complete code string
        full_code = "".join(word_codes)
        
        if not full_code:
            return results  # No code, no matches
        
        # Step 3: Get all possible meter indices
        # Start with all regular meters
        all_meter_indices = list(range(NUM_METERS))
        
        # Add varied meters if any
        if NUM_VARIED_METERS > 0:
            all_meter_indices.extend(range(NUM_METERS, NUM_METERS + NUM_VARIED_METERS))
        
        # Add rubai meters
        if NUM_RUBAI_METERS > 0:
            all_meter_indices.extend(range(
                NUM_METERS + NUM_VARIED_METERS,
                NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
            ))
        
        # Step 4: Filter meters by code length
        matching_meters = check_code_length(full_code, all_meter_indices)
        
        # Step 5: For each matching meter, verify pattern match and create scanOutput
        for meter_idx in matching_meters:
            # Get meter pattern
            if meter_idx < NUM_METERS:
                meter_pattern = METERS[meter_idx]
                meter_name = METER_NAMES[meter_idx]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
                meter_name = METERS_VARIED_NAMES[meter_idx - NUM_METERS]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
                meter_name = RUBAI_METER_NAMES[meter_idx - NUM_METERS - NUM_VARIED_METERS] + " (رباعی)"
            else:
                continue  # Skip invalid indices
            
            # Verify pattern match: check if full code matches meter pattern
            # Create meter variations and check if code matches any
            meter_clean = meter_pattern.replace("/", "")
            meter1 = meter_clean.replace("+", "")
            meter2 = meter_clean.replace("+", "") + "-"
            meter3 = meter_clean.replace("+", "-") + "-"
            meter4 = meter_clean.replace("+", "-")
            
            matches = False
            
            # Check against all 4 variations
            for meter_var in [meter1, meter2, meter3, meter4]:
                if len(meter_var) == len(full_code):
                    match = True
                    for j in range(len(meter_var)):
                        met_char = meter_var[j]
                        code_char = full_code[j]
                        if met_char == '-':
                            if code_char != '-' and code_char != 'x':
                                match = False
                                break
                        elif met_char == '=':
                            if code_char != '=' and code_char != 'x':
                                match = False
                                break
                    if match:
                        matches = True
                        break
            
            if matches:
                # Create scanOutput
                so = scanOutput()
                so.original_line = line.original_line
                so.words = line.words_list.copy()
                so.word_taqti = word_codes.copy()
                so.word_muarrab = [w.word for w in line.words_list]  # Use original word as muarrab for now
                so.meter_name = meter_name
                so.feet = afail(meter_pattern)  # Get feet breakdown
                so.id = meter_idx
                so.num_lines = 1
                
                results.append(so)
        
        return results
    
    def scan_lines(self) -> List[scanOutput]:
        """
        Main method to process all lines and return scan outputs.
        
        This method processes all lines added to the scansion engine,
        assigns codes using heuristics, matches against meters, and
        returns all possible scan outputs.
        
        Returns:
            List of scanOutput objects, one per line per matching meter
        """
        all_results: List[scanOutput] = []
        
        if self.free_verse or self.fuzzy:
            # For Phase 1, we don't handle free verse or fuzzy matching
            return all_results
        
        # Process each line
        for k in range(self.num_lines):
            line = self.lst_lines[k]
            line_results = self.scan_line(line, k)
            all_results.extend(line_results)
        
        return all_results
