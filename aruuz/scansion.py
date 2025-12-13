"""
Core scansion engine for Urdu poetry.

This module contains the main Scansion class that processes
Urdu poetry lines and identifies meters.
"""

from typing import List
from aruuz.models import Words
from aruuz.utils.araab import remove_araab, ARABIC_DIACRITICS


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
