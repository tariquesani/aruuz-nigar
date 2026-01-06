"""
Core scansion engine for Urdu poetry.

This module contains the main Scansion class that processes
Urdu poetry lines and identifies meters.
"""

import math
import warnings
from typing import List, Optional, Tuple
from aruuz.models import Words, Lines, scanOutput, scanOutputFuzzy, scanPath, codeLocation
from aruuz.utils.araab import remove_araab, ARABIC_DIACRITICS
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS, SPECIAL_METERS,
    METER_NAMES, METERS_VARIED_NAMES, RUBAI_METER_NAMES, SPECIAL_METER_NAMES,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, NUM_SPECIAL_METERS,
    afail, afail_list, meter_index, afail_hindi, zamzama_feet, hindi_feet
)
from aruuz.database.word_lookup import WordLookup
from aruuz.tree.code_tree import CodeTree


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


def is_izafat(word: str) -> bool:
    """
    Check if last character is izafat marker.
    
    Checks if the last character is:
    - ARABIC_DIACRITICS[1] (zer, \u0650)
    - ARABIC_DIACRITICS[10] (izafat, \u0654)
    - \u06C2 (ۂ)
    
    Args:
        word: Word to check
        
    Returns:
        True if last character is an izafat marker, False otherwise
    """
    if not word or len(word) == 0:
        return False
    
    last_char = word[-1]
    return (last_char == ARABIC_DIACRITICS[1] or 
            last_char == ARABIC_DIACRITICS[10] or 
            last_char == '\u06C2')


def is_consonant_plus_consonant(word: str) -> bool:
    """
    Check if positions 0 and 1 are both consonants (not ا،ی،ے،ہ).
    
    This function checks if both the first and second characters of the word
    are consonants, meaning they are NOT one of the vowel characters:
    ا (alif), ی (ye), ے (ye barree), or ہ (heh).
    
    Args:
        word: Word to check
        
    Returns:
        True if both positions 0 and 1 are consonants, False otherwise.
        Returns False if word length is less than 2.
    """
    if not word or len(word) < 2:
        return False
    
    # Check if position 1 is NOT a vowel
    if not (word[1] == 'ا' or word[1] == 'ی' or word[1] == 'ے' or word[1] == 'ہ'):
        # Check if position 0 is NOT a vowel
        if not (word[0] == 'ا' or word[0] == 'ی' or word[0] == 'ے' or word[0] == 'ہ'):
            return True
        else:
            return False
    else:
        return False


def remove_tashdid(word: str) -> str:
    """
    Remove shadd diacritic by replacing it with appropriate diacritics.
    
    This function processes shadd (ARABIC_DIACRITICS[0]) and replaces it
    with appropriate diacritics (jazm + char + paish) based on context.
    Only processes words that contain diacritical marks (muarrab).
    
    Args:
        word: Word that may contain shadd diacritic
        
    Returns:
        Modified word with shadd replaced, or original word if not muarrab
    """
    # Only process if word is muarrab (has diacritics)
    if not is_muarrab(word):
        return word
    
    wrd = ""
    for i in range(len(word)):
        if word[i] == ARABIC_DIACRITICS[0]:  # shadd
            if i - 2 >= 0:  # There are at least 2 characters before this shadd
                # Check if character at i-2 is NOT a diacritic
                if word[i - 2] not in ARABIC_DIACRITICS:
                    # Check if character at i-1 is NOT a diacritic
                    if word[i - 1] not in ARABIC_DIACRITICS:
                        # Remove last character from wrd, then add replacement
                        if len(wrd) > 0:
                            wrd = wrd[:-1]
                        wrd += word[i - 1] + ARABIC_DIACRITICS[2] + word[i - 1] + ARABIC_DIACRITICS[8]
                    else:
                        # word[i-1] IS a diacritic
                        # Remove last 2 characters from wrd, then add replacement
                        if len(wrd) >= 2:
                            wrd = wrd[:-2]
                        wrd += word[i - 2] + ARABIC_DIACRITICS[2] + word[i - 2] + ARABIC_DIACRITICS[8]
                else:
                    # word[i-2] IS a diacritic
                    wrd += ARABIC_DIACRITICS[2] + word[i - 1] + ARABIC_DIACRITICS[8]
            else:
                # i - 2 < 0, not enough characters before shadd
                # Need at least i-1 >= 0 to access word[i-1]
                if i - 1 >= 0:
                    wrd += ARABIC_DIACRITICS[2] + word[i - 1] + ARABIC_DIACRITICS[8]
        else:
            # Not a shadd, add character as-is
            wrd += word[i]
    
    return wrd


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
                    # If alif is followed by hamza/ye ending, final syllable is ambiguous
                    if 'ئ' in stripped[3:] or stripped.endswith('ے'):
                        code = "-=x"
                    else:
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


def is_match(meter: str, tentative_code: str, word_code: str) -> bool:
    """
    Check if a meter pattern matches a code sequence.
    
    .. deprecated:: 
        This function is deprecated. Use the tree-based matching via 
        `CodeTree._is_match()` or `Scansion.find_meter()` instead.
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
        "or Scansion.find_meter() instead. This function will be removed in a future version.",
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
        `CodeTree._check_code_length()` or `Scansion.find_meter()` instead.
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
        "CodeTree._check_code_length() or Scansion.find_meter() instead. "
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


class Scansion:
    """
    Main scansion engine for Urdu poetry.
    
    This class processes lines of Urdu poetry, assigns scansion codes to words,
    and matches them against meter patterns.
    """
    
    def __init__(self, word_lookup: Optional[WordLookup] = None):
        """
        Initialize a new Scansion instance.
        
        Args:
            word_lookup: Optional WordLookup instance for database access.
                        If not provided, creates a WordLookup instance internally.
                        If database is unavailable, gracefully handles the error.
        """
        self.lst_lines: List[Lines] = []
        self.num_lines: int = 0
        self.is_checked: bool = False
        self.free_verse: bool = False
        self.fuzzy: bool = False
        self.error_param: int = 8
        self.meter: Optional[List[int]] = None
        
        # Initialize word_lookup for database access
        if word_lookup is not None:
            self.word_lookup = word_lookup
        else:
            # Create WordLookup instance internally with graceful fallback
            try:
                self.word_lookup = WordLookup()
            except Exception:
                # If database is unavailable, set to None
                # Methods using word_lookup should check for None before use
                self.word_lookup = None
    
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
        Assign scansion code to a word using database lookup (if available) or heuristics.
        
        This method:
        1. Tries database lookup first (if available)
        2. Falls back to heuristics using the assign_code function
        3. If heuristics fail (empty code) and word length > 4, tries compound word splitting
        
        Args:
            word: Words object to assign code to
            
        Returns:
            Words object with code assigned
        """
        # If word already has codes, return as is
        if len(word.code) > 0:
            return word
        
        # Strategy 1: Try database lookup first (if available)
        if self.word_lookup is not None:
            try:
                word = self.word_lookup.find_word(word)
                
                # If database lookup found results
                if len(word.id) > 0:
                    # Apply special 3-character word handling
                    word = self._apply_db_word_variations(word)
                    return word
            except Exception:
                # On any DB error, fall back to heuristics
                pass
        
        # Strategy 2: Fallback to heuristics
        code = assign_code(word)
        
        # Strategy 3: Try compound word splitting if heuristics failed
        # C#: if (stripped.Length > 4 && code.Equals(""))
        stripped = remove_araab(word.word)
        if len(stripped) > 4 and code == "":
            # Try compound word splitting
            word_result = self.compound_word(word)
            # If compound_word found a valid split (has codes), use it
            if len(word_result.code) > 0:
                return word_result
            # Otherwise, continue with empty code (will be stored below)
        
        # Store code in word
        word.code = [code]
        
        return word
    
    def _apply_db_word_variations(self, word: Words) -> Words:
        """
        Apply special 3-character word handling for DB results.
        
        Mirrors C# logic (lines 1846-1869) for post-processing database results.
        
        For 3-character words ending in 'ا' (alif):
        - If word starts with 'آ': add alternative code "==" or "=x" if not already present
        - If word doesn't start with 'آ': add alternative code "-=" or "-x" if not already present
        
        Args:
            word: Words object from database lookup
            
        Returns:
            Words object with additional code variations if applicable
        """
        # Remove araab and special characters (ھ \u06BE and ں \u06BA) for scansion purposes
        # C#: string subString = Araab.removeAraab(wrd.word.Replace("\u06BE", "").Replace("\u06BA", ""));
        sub_string = word.word.replace("\u06BE", "").replace("\u06BA", "")
        sub_string = remove_araab(sub_string)
        
        # C#: if (subString.Length == 3)
        if len(sub_string) == 3:
            # C#: if(subString[2] == 'ا')
            if sub_string[2] == 'ا':  # Third character is alif
                # C#: if (subString[0] == 'آ')
                if sub_string[0] == 'آ':  # First character is alif madd
                    # C#: if (!wrd.code[0].Equals("==") && !wrd.code[0].Equals("=x"))
                    if len(word.code) > 0 and word.code[0] != "==" and word.code[0] != "=x":
                        # C#: wrd.id.Add(-1);
                        # C#: wrd.code.Add("==");
                        word.id.append(-1)
                        word.code.append("==")
                else:  # First character is not alif madd
                    # C#: if (!wrd.code[0].Equals("-=") && !wrd.code[0].Equals("-x"))
                    if len(word.code) > 0 and word.code[0] != "-=" and word.code[0] != "-x":
                        # C#: wrd.id.Add(-1);
                        # C#: wrd.code.Add("-=");
                        word.id.append(-1)
                        word.code.append("-=")
        
        return word
    
    def plural_form(self, substr: str, len_param: int) -> Words:
        """
        Handle plural forms by removing suffix and trying base form.
        
        Removes araab, strips "ال" prefix if present, removes last `len_param`
        characters, then tries base form and base + "نا".
        
        Args:
            substr: Word substring to process
            len_param: Number of characters to remove from end
            
        Returns:
            Words object with populated id list if found in database
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return empty Words
            wrd = Words()
            wrd.word = substr
            return wrd
        
        wrd = Words()
        wrd.word = substr
        substr = remove_araab(substr)
        
        # Strip "ال" prefix if present (matching C#: substr[0] == 'ا' && substr[1] == 'ل')
        if len(substr) >= 2 and substr[0] == 'ا' and substr[1] == 'ل':
            substr = substr[2:]
        
        # Remove last len_param characters to get base form
        # C#: substr.Remove(substr.Length - len, len) → Python: substr[:-len_param]
        form1 = substr[:-len_param] if len(substr) > len_param else substr
        form2 = form1 + "نا"
        
        # Try form1 first
        wrd.word = form1
        wrd = self.word_lookup.find_word(wrd)
        
        # If not found, try form2
        if len(wrd.id) == 0:
            wrd.word = form2
            wrd = self.word_lookup.find_word(wrd)
        
        return wrd
    
    def plural_form_noon_ghunna(self, substr: str) -> Words:
        """
        Handle plural forms with noon ghunna.
        
        Removes araab, strips "ال" prefix if present, then searches for word as-is.
        
        Args:
            substr: Word substring to process
            
        Returns:
            Words object with populated id list if found in database
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return empty Words
            wrd = Words()
            wrd.word = substr
            return wrd
        
        wrd = Words()
        wrd.word = substr
        substr = remove_araab(substr)
        
        # Strip "ال" prefix if present
        if len(substr) >= 2 and substr[0] == 'ا' and substr[1] == 'ل':
            substr = substr[2:]
        
        # Search for word as-is
        wrd.word = substr
        wrd = self.word_lookup.find_word(wrd)
        
        return wrd
    
    def plural_form_aat(self, substr: str) -> Words:
        """
        Handle plurals ending in -ات (aat).
        
        Tries multiple forms:
        1. Base form (remove last 2 chars)
        2. Base + "ہ"
        3. Remove last 2 chars but keep 2nd-to-last char
        4. If ends in "یات", remove last 3 chars but keep 3rd-to-last char
        5. form5 (never initialized in C#, so this won't match)
        
        Args:
            substr: Word substring to process (should end in -ات)
            
        Returns:
            Words object with populated id list if found in database
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return empty Words
            wrd = Words()
            wrd.word = substr
            return wrd
        
        wrd = Words()
        wrd.word = substr
        substr = remove_araab(substr)
        
        # Strip "ال" prefix if present
        if len(substr) >= 2 and substr[0] == 'ا' and substr[1] == 'ل':
            substr = substr[2:]
        
        length = len(substr)
        
        # form1: Remove last 2 characters (تصورات)
        # C#: substr.Remove(substr.Length - 2, 2) → Python: substr[:-2]
        form1 = substr[:-2] if length >= 2 else substr
        # form2: form1 + "ہ" (نظریہ،کلیہ)
        form2 = form1 + "ہ"
        # form3: Remove last 2 chars, but only 1 char (keep 2nd-to-last)
        # C#: substr.Remove(substr.Length - 2, 1) → Python: substr[:length-2] + substr[length-1:]
        form3 = substr[:length-2] + substr[length-1:] if length >= 2 else substr
        # form4: Remove last 3 chars, but only 1 char (keep 3rd-to-last)
        # C#: substr.Remove(substr.Length - 3, 1) → Python: substr[:length-3] + substr[length-2:]
        form4 = substr[:length-3] + substr[length-2:] if length >= 3 else substr
        # form5: Never initialized in C# code, but declared as empty string
        form5 = ""
        
        # Try form1 first
        wrd.word = form1
        wrd = self.word_lookup.find_word(wrd)
        
        if len(wrd.id) == 0:
            # Try form2
            wrd.word = form2
            wrd = self.word_lookup.find_word(wrd)
            if len(wrd.id) == 0:
                # Try form3
                wrd.word = form3
                wrd = self.word_lookup.find_word(wrd)
                if len(wrd.id) == 0:
                    # Check if ends in "یات" before trying form4
                    # C#: substr[length - 1] == 'ت' && substr[length - 2] == 'ا' && substr[length - 3] == 'ی'
                    if length >= 3 and substr[length - 1] == 'ت' and substr[length - 2] == 'ا' and substr[length - 3] == 'ی':
                        wrd.word = form4
                        wrd = self.word_lookup.find_word(wrd)
                        if len(wrd.id) == 0:
                            # Try form5 (though it's empty, matching C# behavior)
                            wrd.word = form5
                            wrd = self.word_lookup.find_word(wrd)
        
        return wrd
    
    def plural_form_aan(self, substr: str) -> Words:
        """
        Handle plurals ending in -ان (aan).
        
        Tries multiple forms:
        1. Base form (remove last 2 chars)
        2. Base + "ہ"
        3. Base + "ا"
        4. Base + "نا"
        
        Args:
            substr: Word substring to process (should end in -ان)
            
        Returns:
            Words object with populated id list if found in database
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return empty Words
            wrd = Words()
            wrd.word = substr
            return wrd
        
        wrd = Words()
        wrd.word = substr
        substr = remove_araab(substr)
        
        # Strip "ال" prefix if present
        if len(substr) >= 2 and substr[0] == 'ا' and substr[1] == 'ل':
            substr = substr[2:]
        
        length = len(substr)
        
        # form1: Remove last 2 characters (لڑکیاں)
        form1 = substr[:-2] if length >= 2 else substr
        # form2: form1 + "ہ" (رستوں)
        form2 = form1 + "ہ"
        # form3: form1 + "ا" (سودوں)
        form3 = form1 + "ا"
        # form4: form1 + "نا" (دکھاوں)
        form4 = form1 + "نا"
        
        # Try form1 first
        wrd.word = form1
        wrd = self.word_lookup.find_word(wrd)
        
        if len(wrd.id) == 0:
            # Try form2
            wrd.word = form2
            wrd = self.word_lookup.find_word(wrd)
            if len(wrd.id) == 0:
                # Try form3
                wrd.word = form3
                wrd = self.word_lookup.find_word(wrd)
                if len(wrd.id) == 0:
                    # Try form4
                    wrd.word = form4
                    wrd = self.word_lookup.find_word(wrd)
        
        return wrd
    
    def plural_form_ye(self, substr: str) -> Words:
        """
        Handle plurals ending in -ی (ye).
        
        Tries multiple forms:
        1. Base + "نا" (where base = remove last 2 chars)
        2. Base (remove last 2 chars)
        
        Args:
            substr: Word substring to process (should end in -ی)
            
        Returns:
            Words object with populated id list if found in database
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return empty Words
            wrd = Words()
            wrd.word = substr
            return wrd
        
        wrd = Words()
        wrd.word = substr
        substr = remove_araab(substr)
        
        # Strip "ال" prefix if present
        if len(substr) >= 2 and substr[0] == 'ا' and substr[1] == 'ل':
            substr = substr[2:]
        
        length = len(substr)
        
        # form1: Remove last 2 chars, then add "نا" (ستائے)
        # C#: substr.Remove(substr.Length - 2, 2) + "نا"
        form1 = (substr[:-2] if length >= 2 else substr) + "نا"
        # form2: Remove last 2 chars (استغنائے)
        form2 = substr[:-2] if length >= 2 else substr
        
        # Try form1 first
        wrd.word = form1
        wrd = self.word_lookup.find_word(wrd)
        
        # If not found, try form2
        if len(wrd.id) == 0:
            wrd.word = form2
            wrd = self.word_lookup.find_word(wrd)
        
        return wrd
    
    def plural_form_postfix_aan(self, substr: str) -> Words:
        """
        Handle plurals with -ان postfix.
        
        Removes last 2 characters (the -ان suffix) and searches for base form.
        
        Args:
            substr: Word substring to process (should end in -ان)
            
        Returns:
            Words object with populated id list if found in database
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return empty Words
            wrd = Words()
            wrd.word = substr
            return wrd
        
        wrd = Words()
        wrd.word = substr
        substr = remove_araab(substr)
        
        # Strip "ال" prefix if present
        if len(substr) >= 2 and substr[0] == 'ا' and substr[1] == 'ل':
            substr = substr[2:]
        
        length = len(substr)
        
        # form1: Remove last 2 characters
        form1 = substr[:-2] if length >= 2 else substr
        
        # Search for base form
        wrd.word = form1
        wrd = self.word_lookup.find_word(wrd)
        
        return wrd
    
    def compound_word(self, wrd: Words) -> Words:
        """
        Attempt to split a word into compound parts and combine their codes.
        
        This method tries to split a word at various positions and:
        1. Uses find_word() on the first part (database lookup)
        2. Uses word_code() on the second part (heuristics)
        3. If both parts are valid, combines codes and muarrab via cartesian product
        
        Args:
            wrd: Words object containing the word to process
            
        Returns:
            Words object with combined codes and muarrab, with modified=True if successful
        """
        if self.word_lookup is None:
            # If word_lookup is unavailable, return original word with modified flag
            wd = Words()
            wd.word = wrd.word
            wd.modified = True
            return wd
        
        wd = Words()
        wd.word = wrd.word
        stripped = remove_araab(wrd.word)
        
        # Iterate through possible split points (1 to length-2)
        # C#: for (int i = 1; i < stripped.Length - 1; i++)
        # This means i goes from 1 to stripped.Length - 2 (inclusive)
        for i in range(1, len(stripped) - 1):
            flag = False
            first = Words()
            # First part: from start to i
            # C#: first.word = stripped.Substring(0, i)
            first.word = stripped[:i]
            # Use find_word() on first part (database lookup)
            first = self.word_lookup.find_word(first)
            
            second = Words()
            # Second part: from i to end
            # C#: second.word = stripped.Substring(i, stripped.Length - i)
            second.word = stripped[i:]
            # Use word_code() on second part (heuristics)
            second = self.word_code(second)
            
            # Check validity (matching C# logic)
            # C#: if (first.id.Count > 0)
            if len(first.id) > 0:
                # C#: if (second.id.Count == 0)
                if len(second.id) == 0:
                    # C#: if (second.word.Length <= 2)
                    if len(second.word) <= 2:
                        # Use length_two_scan() on second part
                        # C#: second.code.Add(lengthTwoScan(second.word))
                        second.code.append(length_two_scan(second.word))
                        # C#: second.id.Add(-1)
                        second.id.append(-1)
                        flag = True
                else:  # Perfect match - both parts found
                    flag = True
            else:
                # C#: if (second.id.Count > 0)
                if len(second.id) > 0:
                    # C#: if (first.word.Length <= 2)
                    if len(first.word) <= 2:
                        # Use length_two_scan() on first part
                        # C#: first.code.Add(lengthTwoScan(first.word))
                        first.code.append(length_two_scan(first.word))
                        # C#: first.id.Add(-1)
                        first.id.append(-1)
                        flag = True
            
            # If flag is True, combine codes and muarrab via cartesian product
            # C#: if (flag)
            if flag:
                # Combine words (matching C#: first.word += "" + second.word)
                first.word = first.word + second.word
                
                # Cartesian product of codes
                # C#: for (int k = 0; k < first.code.Count; k++)
                #      for (int j = 0; j < second.code.Count; j++)
                #          codes.Add(first.code[k] + second.code[j])
                codes = []
                for k in range(len(first.code)):
                    for j in range(len(second.code)):
                        codes.append(first.code[k] + second.code[j])
                first.code = codes
                
                # Cartesian product of muarrab
                # C#: for (int k = 0; k < first.muarrab.Count; k++)
                #      for (int j = 0; j < second.muarrab.Count; j++)
                #          muarrab.Add(first.muarrab[k] + second.muarrab[j])
                muarrab = []
                for k in range(len(first.muarrab)):
                    for j in range(len(second.muarrab)):
                        muarrab.append(first.muarrab[k] + second.muarrab[j])
                first.muarrab = muarrab
                wd = first
                break
        
        # Set modified flag (matching C#: wd.modified = true)
        wd.modified = True
        return wd
    
    def find_meter(self, line: Lines, meters: Optional[List[int]] = None) -> List[scanPath]:
        """
        Build CodeTree from line and find matching meters using tree traversal.
        
        This method builds a tree structure from the word codes in the line and
        uses tree-based traversal to efficiently match against meter patterns.
        This is the main entry point for tree-based pattern matching.
        
        Args:
            line: Lines object containing words with assigned codes
            meters: Optional list of meter indices to check. If None, uses self.meter.
                   If self.meter is also None, checks all meters.
        
        Returns:
            List of scanPath objects representing matching paths through the tree
        """
        # Use self.meter if meters parameter is not provided
        if meters is None:
            meters = self.meter
        
        # Build CodeTree from line
        # The build_from_line method handles both regular codes and taqti_word_graft codes
        tree = CodeTree.build_from_line(
            line,
            error_param=self.error_param,
            fuzzy=self.fuzzy,
            free_verse=self.free_verse
        )
        
        # Call tree.find_meter() to get scanPath results
        return tree.find_meter(meters)
    
    def scan_line(self, line: Lines, line_index: int) -> List[scanOutput]:
        """
        Process a single line and return possible scan outputs using tree-based matching.
        
        This method:
        1. Assigns codes to all words in the line
        2. Uses tree-based find_meter() to find matching meters
        3. Converts scanPath results to scanOutput objects
        
        Args:
            line: Lines object to scan
            line_index: Index of the line (for reference)
            
        Returns:
            List of scanOutput objects representing possible meter matches
        """
        results: List[scanOutput] = []
        
        # Step 1: Assign codes to all words (needed for tree building)
        for word in line.words_list:
            self.word_code(word)
        
        # Step 1.5: Al (ال) Processing
        # Modify codes when next word starts with "ال" and current word ends with zabar or paish
        for i in range(len(line.words_list) - 1):
            wrd = line.words_list[i]
            nwrd = line.words_list[i + 1]
            
            if len(nwrd.word) > 1:
                # Check if next word starts with "ال" (first two chars are 'ا' and 'ل')
                if nwrd.word[0] == 'ا' and nwrd.word[1] == 'ل':
                    # Check if current word ends with zabar (ARABIC_DIACRITICS[8]) or paish (ARABIC_DIACRITICS[9])
                    if len(wrd.word) > 0 and (wrd.word[-1] == ARABIC_DIACRITICS[8] or wrd.word[-1] == ARABIC_DIACRITICS[9]):
                        stripped = remove_araab(wrd.word)
                        length = len(stripped)
                        
                        if length > 0:
                            # Process each code in current word
                            for k in range(len(wrd.code)):
                                if is_vowel_plus_h(stripped[length - 1]):
                                    # Last char is vowel+h: modify ending ("=" or "x" → "=", "-" → "=")
                                    if len(wrd.code[k]) > 0:
                                        last_char = wrd.code[k][-1]
                                        if last_char == "=" or last_char == "x":
                                            wrd.code[k] = wrd.code[k][:-1] + "="
                                        elif last_char == "-":
                                            wrd.code[k] = wrd.code[k][:-1] + "="
                                else:
                                    # Last char is consonant
                                    if length == 2 and is_consonant_plus_consonant(wrd.word):
                                        # 2-char words with consonant+consonant: modify to "=="
                                        if len(wrd.code[k]) > 0:
                                            wrd.code[k] = wrd.code[k][:-1] + "=="
                                    else:
                                        # Otherwise: modify ending ("=" or "x" → "-=", "-" → "=")
                                        if len(wrd.code[k]) > 0:
                                            last_char = wrd.code[k][-1]
                                            if last_char == "=" or last_char == "x":
                                                wrd.code[k] = wrd.code[k][:-1] + "-="
                                            elif last_char == "-":
                                                wrd.code[k] = wrd.code[k][:-1] + "="
                            
                            # Remove first character from all codes in next word
                            for k in range(len(nwrd.code)):
                                if len(nwrd.code[k]) > 0:
                                    nwrd.code[k] = nwrd.code[k][1:]
                            
                            # Update muarrab lists: append "ل" to current word
                            for l in range(len(wrd.muarrab)):
                                wrd.muarrab[l] = wrd.muarrab[l] + "ل"
                            
                            # Update muarrab lists: remove first 2 chars from next word
                            for l in range(len(nwrd.muarrab)):
                                if len(nwrd.muarrab[l]) >= 2:
                                    nwrd.muarrab[l] = nwrd.muarrab[l][2:]
        
        # Step 1.6: Izafat (اضافت) Processing
        # Adjust codes for possessive markers
        for wrd in line.words_list:
            if is_izafat(wrd.word):
                if len(wrd.id) > 0:
                    # Word has database ID
                    count = len(wrd.code)
                    for k in range(count):
                        t_word = remove_araab(wrd.word)
                        
                        # Arabic Monosyllabic Words (2-character words)
                        if wrd.length == 2:
                            wrd.code[k] = "xx"
                        # Words ending in "ا" or "و"
                        elif len(wrd.code[k]) > 0 and (wrd.code[k][-1] == "=" or wrd.code[k][-1] == "x"):
                            if len(t_word) > 0 and (t_word[-1] == 'ا' or t_word[-1] == 'و'):
                                # Modify ending: "=" or "x" → "=x"
                                wrd.code[k] = wrd.code[k][:-1] + "=x"
                            else:
                                # Words ending in "ی"
                                if len(t_word) > 0 and t_word[-1] == 'ی':
                                    # Add alternative code (original + "x")
                                    wrd.code.append(wrd.code[k] + "x")
                                    # Modify current code: "=" or "x" → "-x"
                                    wrd.code[k] = wrd.code[k][:-1] + "-x"
                                else:
                                    # Other cases: "=" or "x" → "-x"
                                    wrd.code[k] = wrd.code[k][:-1] + "-x"
                        # Words ending with "-"
                        elif len(wrd.code[k]) > 0 and wrd.code[k][-1] == "-":
                            # Modify ending: "-" → "x"
                            wrd.code[k] = wrd.code[k][:-1] + "x"
                else:
                    # Word has no database ID
                    for k in range(len(wrd.code)):
                        if len(wrd.code[k]) > 0 and (wrd.code[k][-1] == "=" or wrd.code[k][-1] == "x"):
                            # Modify ending: "=" or "x" → "-x"
                            wrd.code[k] = wrd.code[k][:-1] + "-x"
                        elif len(wrd.code[k]) > 0 and wrd.code[k][-1] == "-":
                            # Modify ending: "-" → "x"
                            wrd.code[k] = wrd.code[k][:-1] + "x"
        
        # Step 1.7: Ataf (عطف) Processing
        # Handle conjunction "و" between words
        for i in range(1, len(line.words_list)):
            wrd = line.words_list[i]
            pwrd = line.words_list[i - 1]
            
            if wrd.word == "و":
                stripped = remove_araab(pwrd.word)
                length = len(stripped)
                
                if length > 0:
                    for k in range(len(pwrd.code)):
                        if is_vowel_plus_h(stripped[length - 1]):
                            # Last char is vowel+h
                            if stripped[length - 1] == 'ا' or stripped[length - 1] == 'ی':
                                # Do nothing as it already in correct form
                                pass
                            elif stripped[length - 1] == 'ے' or stripped[length - 1] == 'و':
                                # Modify code and clear current word codes
                                if len(pwrd.code[k]) > 0:
                                    last_char = pwrd.code[k][-1]
                                    if last_char == "=" or last_char == "x":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            wrd.code[j] = ""
                                    elif last_char == "-":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            wrd.code[j] = ""
                            else:
                                # Other vowels: modify code and clear current word codes
                                if len(pwrd.code[k]) > 0:
                                    last_char = pwrd.code[k][-1]
                                    if last_char == "=" or last_char == "x":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            wrd.code[j] = ""
                                    elif last_char == "-":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            wrd.code[j] = ""
                        else:
                            # Last char is consonant
                            if length == 2 and is_consonant_plus_consonant(remove_araab(pwrd.word)):
                                # 2-char consonant+consonant words: set code to "xx" and clear current word codes
                                pwrd.code[k] = "xx"
                                # Clear all codes in current word ("و")
                                for j in range(len(wrd.code)):
                                    wrd.code[j] = ""
                            else:
                                # Otherwise: modify code and clear current word codes
                                if len(pwrd.code[k]) > 0:
                                    last_char = pwrd.code[k][-1]
                                    if last_char == "=" or last_char == "x":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            wrd.code[j] = ""
                                    elif last_char == "-":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            wrd.code[j] = ""
        
        # Step 1.8: Word Grafting (وصال الف)
        # Create taqti_word_graft codes when word starts with 'ا' or 'آ' following a consonant
        for i in range(1, len(line.words_list)):
            wrd = line.words_list[i]
            prev_word = line.words_list[i - 1]
            
            # Check if current word starts with 'ا' or 'آ'
            if len(wrd.word) > 0 and (wrd.word[0] == 'ا' or wrd.word[0] == 'آ'):
                # Check if previous word's last character is NOT vowel+h
                stripped_prev = remove_araab(prev_word.word)
                if len(stripped_prev) > 0:
                    last_char_prev = stripped_prev[-1]
                    if not is_vowel_plus_h(last_char_prev):
                        # Process each code in previous word
                        for k in range(len(prev_word.code)):
                            if len(prev_word.code[k]) > 0:
                                last_code_char = prev_word.code[k][-1]
                                if last_code_char == '=':
                                    # Create graft code: remove last char, append '-'
                                    graft_code = prev_word.code[k][:-1] + '-'
                                    prev_word.taqti_word_graft.append(graft_code)
                                elif last_code_char == '-':
                                    # Create graft code: remove last char
                                    graft_code = prev_word.code[k][:-1]
                                    prev_word.taqti_word_graft.append(graft_code)
        
        # Step 2: Use tree-based find_meter() to get matching scanPaths
        # find_meter() handles tree building, pattern matching, and meter filtering
        scan_paths = self.find_meter(line)
        
        if not scan_paths:
            return results  # No matches found
        
        # Step 3: Convert scanPath results to scanOutput objects
        for sp in scan_paths:
            if not sp.meters:
                continue  # Skip paths with no matching meters
            
            # Extract words and codes from scanPath location (skip index 0 which is root)
            words_list: List[Words] = []
            word_taqti_list: List[str] = []
            
            for i in range(1, len(sp.location)):
                loc = sp.location[i]
                if loc.word_ref >= 0 and loc.word_ref < len(line.words_list):
                    words_list.append(line.words_list[loc.word_ref])
                    word_taqti_list.append(loc.code)
            
            # Build full code string from word codes
            full_code = "".join(word_taqti_list)
            
            if not full_code:
                continue  # Skip if no code
            
            # Step 4: Create scanOutput for each matching meter
            for meter_idx in sp.meters:
                so = scanOutput()
                so.original_line = line.original_line
                so.words = words_list.copy()
                so.word_taqti = word_taqti_list.copy()
                so.word_muarrab = [w.word for w in words_list]  # Use original word as muarrab
                so.num_lines = 1
                
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
                        # Get scansion code from scanPath and generate feet dynamically
                        if special_idx > 7:
                            # Zamzama meters (indices 8-10)
                            so.feet = zamzama_feet(special_idx, full_code)
                        else:
                            # Hindi meters (indices 0-7)
                            so.feet = hindi_feet(special_idx, full_code)
                        # Fall back to static afail_hindi if dynamic generation failed
                        if not so.feet:
                            so.feet = afail_hindi(so.meter_name)
                        so.feet_list = []  # Special meters don't have standard feet_list
                        so.id = -2 - special_idx
                    else:
                        continue  # Skip invalid special meter index
                else:
                    continue  # Skip invalid meter index
                
                results.append(so)
        
        return results
    
    def _calculate_fuzzy_score(self, code: str, meter_pattern: str) -> Tuple[int, str]:
        """
        Calculate fuzzy score using Levenshtein distance.
        
        Creates 4 meter variations and calculates Levenshtein distance for each,
        returning the minimum distance and the best matching meter variation.
        
        The 4 variations are:
        1. Original meter with '+' removed
        2. Meter with '+' removed + "~" appended
        3. Meter with '+' replaced by "~" + "~" appended
        4. Meter with '+' replaced by "~"
        
        Args:
            code: Scansion code string (e.g., "=-=")
            meter_pattern: Meter pattern string (e.g., "-===/-===/-===/-===")
            
        Returns:
            Tuple of (minimum_distance, best_matching_meter_variation) where:
            - minimum_distance: Minimum Levenshtein distance across all 4 meter variations
            - best_matching_meter_variation: The meter variation with the minimum distance
        """
        # Remove '/' from meter
        meter = meter_pattern.replace("/", "")
        
        # Create 4 variations (must create before removing '+' from meter)
        meter1 = meter.replace("+", "")
        meter2 = meter.replace("+", "") + "~"
        meter3 = meter.replace("+", "~") + "~"
        meter4 = meter.replace("+", "~")
        
        # Create a temporary CodeTree instance to access _levenshtein_distance
        # We can use any codeLocation for initialization
        temp_loc = codeLocation(code="", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        temp_tree = CodeTree(temp_loc)
        temp_tree.error_param = self.error_param
        
        # Calculate Levenshtein distance for each variation
        score1 = temp_tree._levenshtein_distance(meter1, code)
        score2 = temp_tree._levenshtein_distance(meter2, code)
        score3 = temp_tree._levenshtein_distance(meter3, code)
        score4 = temp_tree._levenshtein_distance(meter4, code)
        
        # Find minimum distance and corresponding meter variation
        scores = [(score1, meter1), (score2, meter2), (score3, meter3), (score4, meter4)]
        min_score, best_meter = min(scores, key=lambda x: x[0])
        
        return (min_score, best_meter)
    
    def scan_line_fuzzy(self, line: Lines, line_index: int) -> List[scanOutputFuzzy]:
        """
        Process a single line with fuzzy matching and return fuzzy scan outputs.
        
        This method:
        1. Assigns codes to all words in the line
        2. Temporarily enables fuzzy mode and uses tree-based find_meter() to find matching meters
        3. Converts scanPath results to scanOutputFuzzy objects
        4. Calculates fuzzy scores using Levenshtein distance
        
        Args:
            line: Lines object to scan
            line_index: Index of the line (for reference)
            
        Returns:
            List of scanOutputFuzzy objects representing possible meter matches with scores
        """
        results: List[scanOutputFuzzy] = []
        
        # Step 1: Assign codes to all words (needed for tree building)
        for word in line.words_list:
            self.word_code(word)
        
        # Step 2: Temporarily enable fuzzy mode and use tree-based find_meter()
        # Save original fuzzy state
        original_fuzzy = self.fuzzy
        self.fuzzy = True
        
        try:
            # find_meter() handles tree building with fuzzy mode enabled
            scan_paths = self.find_meter(line)
        finally:
            # Restore original fuzzy state
            self.fuzzy = original_fuzzy
        
        if not scan_paths:
            return results  # No matches found
        
        # Step 3: Convert scanPath results to scanOutputFuzzy objects
        for sp in scan_paths:
            if not sp.meters:
                continue  # Skip paths with no matching meters
            
            # Extract words and codes from scanPath location (skip index 0 which is root)
            words_list: List[Words] = []
            word_taqti_list: List[str] = []
            
            for i in range(1, len(sp.location)):
                loc = sp.location[i]
                if loc.word_ref >= 0 and loc.word_ref < len(line.words_list):
                    words_list.append(line.words_list[loc.word_ref])
                    word_taqti_list.append(loc.code)
            
            # Build full code string from word codes
            full_code = "".join(word_taqti_list)
            
            if not full_code:
                continue  # Skip if no code
            
            # Step 4: Create scanOutputFuzzy for each matching meter
            for meter_idx in sp.meters:
                so = scanOutputFuzzy()
                so.original_line = line.original_line
                so.words = words_list.copy()
                so.word_taqti = word_taqti_list.copy()
                so.original_taqti = word_taqti_list.copy()  # Same as word_taqti for now
                so.error = [False] * len(words_list)  # Initialize error flags
                
                # Determine meter pattern, name, and feet based on meter index
                meter_pattern = ""
                if meter_idx < NUM_METERS:
                    # Regular meter
                    meter_pattern = METERS[meter_idx]
                    so.meter_name = METER_NAMES[meter_idx]
                    so.feet = afail(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                    # Varied meter
                    meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
                    so.meter_name = METERS_VARIED_NAMES[meter_idx - NUM_METERS]
                    so.feet = afail(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                    # Rubai meter
                    meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
                    so.meter_name = RUBAI_METER_NAMES[meter_idx - NUM_METERS - NUM_VARIED_METERS] + " (رباعی)"
                    so.feet = afail(meter_pattern)
                    so.id = -2
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS + NUM_SPECIAL_METERS:
                    # Special meter (Hindi/Zamzama)
                    special_idx = meter_idx - NUM_METERS - NUM_VARIED_METERS - NUM_RUBAI_METERS
                    if special_idx < len(SPECIAL_METER_NAMES):
                        so.meter_name = SPECIAL_METER_NAMES[special_idx]
                        # Get scansion code from scanPath and generate feet dynamically
                        if special_idx > 7:
                            # Zamzama meters (indices 8-10)
                            so.feet = zamzama_feet(special_idx, full_code)
                        else:
                            # Hindi meters (indices 0-7)
                            so.feet = hindi_feet(special_idx, full_code)
                        # Fall back to static afail_hindi if dynamic generation failed
                        if not so.feet:
                            so.feet = afail_hindi(so.meter_name)
                        so.id = -2 - special_idx
                        # For special meters, we don't have a standard pattern, so skip score calculation
                        so.score = 10  # Default score
                    else:
                        continue  # Skip invalid special meter index
                else:
                    continue  # Skip invalid meter index
                
                # Calculate fuzzy score using Levenshtein distance
                # Only calculate if we have a meter pattern
                if meter_pattern:
                    min_distance, best_meter = self._calculate_fuzzy_score(full_code, meter_pattern)
                    so.score = min_distance
                
                # Initialize meter_syllables and code_syllables (can be populated later if needed)
                so.meter_syllables = []
                so.code_syllables = []
                
                results.append(so)
        
        return results
    
    def scan_lines_fuzzy(self) -> List[scanOutputFuzzy]:
        """
        Process all lines with fuzzy matching and return consolidated fuzzy scan outputs.
        
        This method:
        1. Iterates through all lines in self.lst_lines
        2. Calls scan_line_fuzzy() for each line
        3. Collects all scanOutputFuzzy results
        4. Calls crunch_fuzzy() to consolidate results
        5. Returns List[scanOutputFuzzy]
        
        Returns:
            List of scanOutputFuzzy objects for all lines, consolidated by best meter
        """
        all_results: List[scanOutputFuzzy] = []
        
        # Process each line
        for k in range(self.num_lines):
            line = self.lst_lines[k]
            line_results = self.scan_line_fuzzy(line, k)
            all_results.extend(line_results)
        
        # Consolidate results: crunch_fuzzy() returns only results matching best meter
        if all_results:
            all_results = self.crunch_fuzzy(all_results)
        
        return all_results
    
    def is_ordered(self, line_arkaan: List[str], feet: List[str]) -> bool:
        """
        Check if line feet are in the same order as meter feet.
        
        Args:
            line_arkaan: List of feet from the line (e.g., ["مفعولن", "مفعولن"])
            feet: List of feet from the meter (e.g., ["مفعولن", "مفعولن"])
            
        Returns:
            True if feet are in the same order, False otherwise
        """
        if len(line_arkaan) != len(feet):
            return False
        
        for i in range(len(line_arkaan)):
            if line_arkaan[i] != feet[i]:
                return False
        
        return True
    
    def calculate_score(self, meter: str, line_feet: str) -> int:
        """
        Calculate score for how well a line matches a meter.
        
        This method evaluates how well a poetry line's feet match against all
        variants of a given meter pattern. It parses the line's feet, retrieves
        all meter variants for the given meter name, and evaluates each variant
        separately to find the best match.
        
        The score represents the number of feet that match in the correct order
        against the best matching meter variant. Each meter variant is evaluated
        independently, and the maximum score across all variants is returned.
        
        Args:
            meter: Meter name string (e.g., "مفعولن مفعولن مفعولن مفعولن")
            line_feet: Space-separated string of feet from the scanned line
                      (e.g., "مفعولن مفعولن مفعولن مفعولن")
        
        Returns:
            Integer score representing the number of matching feet in correct order.
            Returns 0 if:
            - No meter variants found for the given meter name
            - No meter variant has matching length with the line
            - No feet match in order
            Otherwise returns the maximum score (1 to number of feet) across all variants.
        
        Note:
            This method evaluates each meter variant separately. A meter name may
            have multiple variants (e.g., with different '+' positions), and the
            score is calculated for each variant independently. The method requires
            that the line feet and meter feet have the same length (hard structural
            constraint) before evaluating the match.
        """
        meter_indices = meter_index(meter)

        if not meter_indices:
            return 0

        # Parse line feet (DO NOT deduplicate)
        line_arkaan = []
        for s in line_feet.split(' '):
            s = s.strip()
            if s:
                line_arkaan.append(s)

        best_score = 0

        # IMPORTANT CHANGE: evaluate EACH meter variant separately
        for m_idx in meter_indices:
            if m_idx >= len(METERS):
                continue

            # Get feet for THIS meter variant only
            meter_feet = []
            for s in afail(METERS[m_idx]).split(' '):
                s = s.strip()
                if s:
                    meter_feet.append(s)

            # Hard structural constraint
            if len(line_arkaan) != len(meter_feet):
                continue

            score = self.ordered_match_count(line_arkaan, meter_feet)
            best_score = max(best_score, score)

        return best_score


    def ordered_match_count(self, line_feet: List[str], meter_feet: List[str]) -> int:
        """
        Count how many feet from line_feet appear in meter_feet in correct relative order.
        
        This method implements a greedy matching algorithm that counts consecutive
        matching feet starting from the beginning. It iterates through line_feet
        and tries to find each foot in meter_feet, maintaining the relative order.
        The matching stops at the first foot that cannot be found in the correct
        position, and returns the count of successfully matched feet up to that point.
        
        The algorithm ensures that:
        1. Feet must match exactly (string equality)
        2. Feet must appear in the same relative order in both lists
        3. Matching is greedy (each line foot is matched to the first available
           meter foot that hasn't been matched yet)
        4. Matching stops at the first failure (no backtracking)
        
        Args:
            line_feet: List of foot strings from the scanned poetry line
                      (e.g., ["مفعولن", "مفعولن", "فاعلن"])
            meter_feet: List of foot strings from the meter pattern
                       (e.g., ["مفعولن", "مفعولن", "مفعولن", "مفعولن"])
        
        Returns:
            Integer count of feet that matched in order (0 to len(line_feet)).
            Returns 0 if the first foot doesn't match, or the number of consecutive
            matching feet from the start of the list.
        
        Example:
            If line_feet = ["مفعولن", "مفعولن", "فاعلن"]
            and meter_feet = ["مفعولن", "مفعولن", "مفعولن", "مفعولن"]
            Returns 2 (first two feet match)
            
            If line_feet = ["مفعولن", "فاعلن", "مفعولن"]
            and meter_feet = ["مفعولن", "مفعولن", "فاعلن"]
            Returns 1 (only first foot matches, second doesn't match at position 1)
        """
        count = 0
        j = 0
        matches = []

        for f in line_feet:
            found_match = False
            while j < len(meter_feet):
                if f == meter_feet[j]:
                    count += 1
                    matches.append(f"'{f}' at position {j}")
                    j += 1
                    found_match = True
                    break
                j += 1
            if not found_match:
                # No match found for this foot, stop counting
                break
        return count

    
    def crunch(self, results: List[scanOutput]) -> List[scanOutput]:
        """
        Consolidate multiple meter matches and return only those matching dominant meter.
        
        Algorithm:
        1. Collect all unique meter names from results
        2. Score each meter by summing calculateScore() for all matching lines
        3. Sort scores and meter names together (maintain pairing)
        4. Select meter with highest score
        5. Return all scanOutput objects matching the selected meter
        
        Args:
            results: List of scanOutput objects (multiple matches per line)
            
        Returns:
            List of scanOutput objects for the dominant meter only
        """
        if not results:
            return []
        
        # Collect unique meter names (matching C# logic)
        meter_names = []
        for item in results:
            if item.meter_name:
                # Check if already in list
                found = False
                for existing in meter_names:
                    if existing == item.meter_name:
                        found = True
                        break
                if not found:
                    meter_names.append(item.meter_name)
        
        if not meter_names:
            return []
        
        # Score each meter
        scores = [0.0] * len(meter_names)
        for i, meter_name in enumerate(meter_names):
            for item in results:
                if item.meter_name == meter_name:
                    scores[i] += self.calculate_score(meter_name, item.feet)
        
        # Sort scores and meter names together (maintain pairing)
        # Create list of tuples, sort by score, then extract
        paired = list(zip(scores, meter_names))
        paired.sort(key=lambda x: x[0])  # Sort by score (ascending)
        
        # Get the meter with highest score (last after sort)
        final_meter = paired[-1][1] if paired else ""

        # max_score = max(scores)
        # candidates = [
        #     meter_name
        #     for score, meter_name in zip(scores, meter_names)
        #     if score == max_score
        # ]

        # final_meter = candidates[0]  # earliest = first misra
        
        if not final_meter:
            return []
        
        # Filter results: return only scanOutput objects matching final_meter
        filtered_results = []
        for item in results:
            if item.meter_name == final_meter:
                filtered_results.append(item)
        
        return filtered_results
    
    def crunch_fuzzy(self, results: List[scanOutputFuzzy]) -> List[scanOutputFuzzy]:
        """
        Consolidate fuzzy matching results and return only those matching the best meter.
        
        Algorithm (matching C# crunchFuzzy):
        1. Collect all unique meter names from results
        2. For each meter, calculate aggregate score using logarithmic averaging:
           score = exp(sum(log(scores)) / count) - subtract
           where subtract is the count of zero scores
        3. Handle score == 0 case (add 1 before log, increment subtract)
        4. Sort meters by score (lowest is best for Levenshtein distance)
        5. Select meter with best (lowest) score
        6. Filter results to return only those matching the selected meter
        7. Handle special IDs (-2 for rubai, < 0 for special meters)
        
        Args:
            results: List of scanOutputFuzzy objects (multiple matches per line)
            
        Returns:
            List of scanOutputFuzzy objects for the best meter only
        """
        if not results:
            return []
        
        # Collect unique meter names (matching C# logic)
        meter_names = []
        for item in results:
            if item.meter_name:
                # Check if already in list
                found = False
                for existing in meter_names:
                    if existing == item.meter_name:
                        found = True
                        break
                if not found:
                    meter_names.append(item.meter_name)
        
        if not meter_names:
            return []
        
        # Calculate aggregate score for each meter using logarithmic averaging
        scores = [0.0] * len(meter_names)
        for i, meter_name in enumerate(meter_names):
            score_sum = 0.0
            subtract = 0.0
            count = 0.0
            
            for item in results:
                if item.meter_name == meter_name:
                    if item.score == 0:
                        # Handle score == 0 case: add 1 before log, increment subtract
                        score_sum += math.log(item.score + 1)
                        count += 1.0
                        subtract += 1.0
                    else:
                        score_sum += math.log(item.score)
                        count += 1.0
            
            if count > 0:
                # Calculate aggregate: exp(sum(log(scores)) / count) - subtract
                scores[i] = math.exp(score_sum / count) - subtract
            else:
                scores[i] = float('inf')  # No scores, set to infinity
        
        # Sort scores and meter names together (maintain pairing)
        # Lower score is better for Levenshtein distance
        # Create parallel arrays like C# Array.Sort(scores, metes)
        paired = list(zip(scores, meter_names))
        paired.sort(key=lambda x: x[0])  # Sort by score (ascending)
        
        # Get the meter with best (lowest) score (first after sort, matching C# metes.First())
        final_meter = paired[0][1] if paired else ""
        
        if not final_meter:
            return []
        
        # Filter results: return only scanOutputFuzzy objects matching final_meter
        # Matching C# logic:
        # - If id == -2: match by meter name
        # - Else if meterIndex(finalMeter).Count > 0: match by id == Meters.id[meterIndex(finalMeter).First()]
        # - Special meters (id < -2) should also match by meter name
        filtered_results = []
        # Get meter indices for the final meter name (for regular meters)
        meter_indices = meter_index(final_meter)
        
        for item in results:
            if item.id == -2:
                # Rubai meter: match by meter name
                if item.meter_name == final_meter:
                    filtered_results.append(item)
            elif item.id < 0:
                # Special meter (id < -2): match by meter name
                if item.meter_name == final_meter:
                    filtered_results.append(item)
            elif meter_indices and len(meter_indices) > 0:
                # Regular or varied meter: match by meter ID using first index
                # In Python, id is the meter index itself, so check if it matches first index
                if item.id == meter_indices[0]:
                    filtered_results.append(item)
            else:
                # Fallback: if meter_index didn't find anything (e.g., varied meter),
                # match by meter name
                if item.meter_name == final_meter:
                    filtered_results.append(item)
        
        return filtered_results
    
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
        
        if self.free_verse:
            # For Phase 1, we don't handle free verse
            return all_results
        
        if self.fuzzy:
            # Use fuzzy matching path
            fuzzy_results = self.scan_lines_fuzzy()
            # Convert scanOutputFuzzy to scanOutput for compatibility
            # Note: This loses fuzzy score information but maintains API compatibility
            all_results = []
            for fr in fuzzy_results:
                so = scanOutput()
                so.original_line = fr.original_line
                so.words = fr.words
                so.word_taqti = fr.word_taqti
                so.meter_name = fr.meter_name
                so.feet = fr.feet
                so.id = fr.id
                so.is_dominant = True  # Fuzzy results are already filtered by crunch_fuzzy
                all_results.append(so)
            return all_results
        
        # Process each line
        for k in range(self.num_lines):
            line = self.lst_lines[k]
            line_results = self.scan_line(line, k)
            all_results.extend(line_results)
        
        # Consolidate results: crunch() returns only results matching dominant meter
        if all_results:
            all_results = self.crunch(all_results)
            # Mark all returned results as dominant (they're already filtered)
            for result in all_results:
                result.is_dominant = True
        
        return all_results
