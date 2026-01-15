"""
Length-Based Scanning Functions

Pure functions for scanning words based on length.
No classes, no state dependencies.
"""

import logging
from aruuz.utils.araab import remove_araab, ARABIC_DIACRITICS
from aruuz.scansion.word_analysis import (
    is_vowel_plus_h,
    is_muarrab,
    locate_araab,
    contains_noon
)

logger = logging.getLogger(__name__)


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


def length_five_scan(word: str) -> str:
    """
    Handle 5+ character words for scansion.
    
    Args:
        substr: Five or more character substring
        
    Returns:
        Scansion code based on character patterns
    """
    logger.debug(f"length_five_scan: Input substring = '{word}'")
    code = ""
    # Remove ھ and ں for scansion purposes
    word_no_aspirate = word.replace("\u06BE", "").replace("\u06BA", "")
    logger.debug(f"length_five_scan: After removing ھ and ں = '{word_no_aspirate}'")
    word_no_diacritics = remove_araab(word_no_aspirate)
    logger.debug(f"length_five_scan: After removing araab (word_no_diacritics) = '{word_no_diacritics}' (length={len(word_no_diacritics)})")
    
    # --- FIX: aspirated + ی should force short medial vowel (e.g. اندھیرے) ---
    if 'ھ' in word:
        for i in range(len(word) - 2):
            if word[i+1] == 'ھ' and word[i+2] == 'ی':
                logger.debug(f"length_five_scan: Early return for aspirated+ی pattern, returning '-=='")
                return "-=="    
    if len(word_no_diacritics) == 3:
        logger.debug(f"length_five_scan: Stripped length is 3, delegating to length_three_scan")
        code = length_three_scan(word)
    elif len(word_no_diacritics) == 4:
        logger.debug(f"length_five_scan: Stripped length is 4, delegating to length_four_scan")
        code = length_four_scan(word)
    else:
        if word_no_diacritics[0] == 'آ':
            # Remove first 2 characters (آ + next) and scan the rest
            remaining = word_no_aspirate[2:] if len(word_no_aspirate) > 2 else ""
            logger.debug(f"length_five_scan: Split at position 2 (آ pattern): prefix='{word_no_aspirate[:2]}', remaining='{remaining}'")
            code = "=" + length_four_scan(remaining)
        elif is_muarrab(word_no_aspirate):
            logger.debug(f"length_five_scan: Word is muarrab (has diacritics), using muarrab path")
            diacritic_positions = locate_araab(word_no_aspirate)
            if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'ا' or word_no_diacritics[2] == 'ا' or word_no_diacritics[3] == 'ا'):  # check alif at position 2,3,4
                # Position 3 Alif
                if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                    # If alif is followed by hamza/ye ending, final syllable is ambiguous
                    if 'ئ' in word_no_diacritics[3:] or word_no_diacritics.endswith('ے'):
                        code = "-=x"
                        logger.debug(f"length_five_scan: Position 3 Alif with hamza/ye ending: code='{code}'")
                    else:
                        code = "-=="
                        logger.debug(f"length_five_scan: Position 3 Alif: code='{code}'")
                # Position 2 Alif
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':
                    if len(diacritic_positions) > 0 and is_muarrab(diacritic_positions[0]):
                        if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                            split_pos = 3
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, muarrab[0] and muarrab[1]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining)
                        else:
                            split_pos = 4
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, muarrab[0] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining)
                    else:
                        if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                            split_pos = 2
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, muarrab[1] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining)
                        else:
                            split_pos = 3
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, no muarrab): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining)
                # Position 4 Alif
                else:
                    code = "==-"
                    if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                         diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                        code = "--=-"
                        logger.debug(f"length_five_scan: Position 4 Alif with zer/zabar/paish at loc[1]: code='{code}'")
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "--=-"
                        logger.debug(f"length_five_scan: Position 4 Alif with jazr at loc[1]: code='{code}'")
                    elif len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                        if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                            code = "==-"
                        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                            code = "==-"
                        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                            code = "==-"
                        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                            code = "==-"
                        else:
                            code = "--=-"
            else:
                if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'و' or word_no_diacritics[2] == 'و' or word_no_diacritics[3] == 'و' or
                                         word_no_diacritics[1] == 'ی' or word_no_diacritics[2] == 'ی' or word_no_diacritics[3] == 'ی'):
                    if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'و' or word_no_diacritics[1] == 'ی'):
                        if len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                            if len(diacritic_positions) > 0 and is_muarrab(diacritic_positions[0]):
                                if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                                    split_pos = 5
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, muarrab[0] and muarrab[1]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining)
                                else:
                                    split_pos = 4
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, muarrab[0] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining)
                            else:
                                if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                                    split_pos = 3
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, muarrab[1] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining)
                                else:
                                    split_pos = 4
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, no muarrab): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining)
                        elif len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                               diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                               diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                                code = "--=-"
                            else:
                                code = "-=="
                        else:
                            if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "=-="
                                elif len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazr
                                    code = "==-"
                                else:
                                    code = "==-"
                            elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "=-="
                                elif len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazr
                                    code = "=---"
                                else:
                                    if len(diacritic_positions) > 2 and is_muarrab(diacritic_positions[2]):
                                        split_pos = 4
                                        remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                        logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr at 2, muarrab[2]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                        code = "=" + length_three_scan(remaining)
                                    else:
                                        split_pos = 3
                                        remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                        logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr at 2, no muarrab[2]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                        code = "=" + length_three_scan(remaining)
                            else:
                                split_pos = 2
                                remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, no jazr at 2): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                code = "=" + length_three_scan(remaining)
                    elif len(word_no_diacritics) > 2 and (word_no_diacritics[2] == 'و' or word_no_diacritics[2] == 'ی'):
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                                diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "-----"  # highly unlikely
                                else:
                                    code = "--=-"
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "-=="
                    elif len(word_no_diacritics) > 3 and (word_no_diacritics[3] == 'و' or word_no_diacritics[3] == 'ی'):
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                                diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "---="  # highly unlikely
                                else:
                                    code = "--=-"
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "==-"
                    else:
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                             diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                             diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                                diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "-----"  # highly unlikely
                                else:
                                    code = "--=-"
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "==-"
                else:
                    if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                         diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ا':
                                code = "---="
                            else:
                                code = "--=-"
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                        else:
                            code = "-=="
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        if len(diacritic_positions) > 0 and is_muarrab(diacritic_positions[0]):
                            split_pos = 4
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            logger.debug(f"length_five_scan: Split at position {split_pos} (no و/ی, jazr at 1, muarrab[0]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining)
                        else:
                            split_pos = 3
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            logger.debug(f"length_five_scan: Split at position {split_pos} (no و/ی, jazr at 1, no muarrab[0]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining)
                    elif len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                          diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                          diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                        code = "=-="
                    # else: empty code (no change)
        elif len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'ا' or word_no_diacritics[2] == 'ا' or word_no_diacritics[3] == 'ا'):  # check alif at position 2,3,4
            logger.debug(f"length_five_scan: Non-muarrab path with alif at position 2,3, or 4")
            # Position 3 Alif
            if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                code = "-=="
                logger.debug(f"length_five_scan: Position 3 Alif (non-muarrab): code='{code}' (no split)")
            # Position 2 Alif
            elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':
                logger.debug(f"length_five_scan: Position 2 Alif (non-muarrab): checking patterns")
                if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ا':
                    code = "==-"
                    logger.debug(f"length_five_scan: Position 2 Alif with alif at 3: code='{code}' (no split)")
                else:
                    if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                        if len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                            code = "=-="
                            logger.debug(f"length_five_scan: Position 2 Alif with vowels at 3 and 4: code='{code}' (no split)")
                        else:
                            code = "==-"
                            logger.debug(f"length_five_scan: Position 2 Alif with vowel at 3: code='{code}' (no split)")
                    elif len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                        code = "=-="
                        logger.debug(f"length_five_scan: Position 2 Alif with vowel at 4: code='{code}' (no split)")
                    else:
                        code = "==-"
                        logger.debug(f"length_five_scan: Position 2 Alif (default): code='{code}' (no split)")
            # Position 4 Alif
            else:
                code = "==-"
                logger.debug(f"length_five_scan: Position 4 Alif (non-muarrab): initial code='{code}'")
                if len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                    if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                        code = "==-"
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                        code = "==-"
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                        code = "==-"
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                        code = "==-"
                    else:
                        code = "--=-"
                    logger.debug(f"length_five_scan: Position 4 Alif with 'ب' at start: code='{code}' (no split)")
        elif len(word_no_diacritics) > 1 and (is_vowel_plus_h(word_no_diacritics[1]) or is_vowel_plus_h(word_no_diacritics[2]) or is_vowel_plus_h(word_no_diacritics[3])):  # check vowels at position 2,3,4
            logger.debug(f"length_five_scan: Non-muarrab path with vowels at position 2,3, or 4")
            # Position 3 Vowel
            if len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                code = "-=="
                if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                    code = "-=="
                logger.debug(f"length_five_scan: Position 3 Vowel: code='{code}' (no split)")
            # Position 2 Vowel
            elif len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                    code = "==-"
                    logger.debug(f"length_five_scan: Position 2 Vowel with vowel at 3: code='{code}' (no split)")
                else:
                    if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                        if len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                            code = "=-="
                            logger.debug(f"length_five_scan: Position 2 Vowel with vowels at 3 and 4: code='{code}' (no split)")
                        else:
                            code = "==-"
                            logger.debug(f"length_five_scan: Position 2 Vowel with vowel at 3: code='{code}' (no split)")
                    elif len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                        code = "=-="
                        logger.debug(f"length_five_scan: Position 2 Vowel with vowel at 4: code='{code}' (no split)")
                    else:
                        code = "==-"
                        logger.debug(f"length_five_scan: Position 2 Vowel (default): code='{code}' (no split)")
            # Position 4 Vowel
            else:
                code = "==-"
                if len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                    if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                        code = "==-"
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                        code = "==-"
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                        code = "==-"
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                        code = "==-"
                    else:
                        code = "--=-"
                if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ت' and len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ی':
                    code = code[:-1] + "="
                logger.debug(f"length_five_scan: Position 4 Vowel: code='{code}' (no split)")
        else:  # consonants
            logger.debug(f"length_five_scan: Non-muarrab path - consonants only")
            code = "==-"
            if len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                    code = "==-"
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                    code = "==-"
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                    code = "==-"
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                    code = "==-"
                else:
                    code = "--=-"
            if len(word_no_diacritics) > 0 and (word_no_diacritics[0] == 'ت' or word_no_diacritics[0] == 'ش'):
                code = "-=="
            if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ت' and len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ی':
                code = code[:-1] + "="
            if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ا':
                code = "-=="
            elif len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                code = "=-="
            logger.debug(f"length_five_scan: Consonants path: code='{code}' (no split)")
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(word_no_diacritics):
        old_code = code
        code = noon_ghunna(word, code)
        if old_code != code:
            logger.debug(f"length_five_scan: Applied noon ghunna adjustment: '{old_code}' -> '{code}'")

    # Apply yaa adjustment if needed
    if code.endswith("==") and word_no_diacritics.endswith("ے"):
        new_code = code[:-1] + "x"
        logger.debug(f"length_five_scan: Applying yaa adjustment: '{code}' -> '{new_code}'")
        code = new_code

    logger.debug(f"length_five_scan: Final code for '{word}' = '{code}'")
    return code
