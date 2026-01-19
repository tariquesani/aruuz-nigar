"""
Length-Based Scanning Functions

Pure functions for scanning words based on length.
No classes, no state dependencies.
"""

import logging
from typing import Optional, List
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


def length_one_scan(word: str, trace: Optional[List[str]] = None) -> str:
    """
    Handle 1-character words for scansion.
    
    Args:
        word: Single character substring
        trace: Optional list to record trace messages
        
    Returns:
        Scansion code: "=" for آ (long), "-" otherwise (short)
    """
    if trace is None:
        trace = []
    trace.append(f"L1S| INPUT_SUBSTRING: substr={word}")
    word_no_diacritics = remove_araab(word)
    if word_no_diacritics == "آ":
        trace.append("L1S| DETECTED_ALIF_MADD: return_code==")
        return "="
    else:
        trace.append("L1S| NO_ALIF_MADD: return_code=-")
        return "-"


def length_two_scan(word: str, trace: Optional[List[str]] = None) -> str:
    """
    Handle 2-character words for scansion.
    
    Two-lettered words ending in ا،ی،ے،و،ہ are treated as flexible.
    
    Args:
        word: Two-character substring
        trace: Optional list to record trace messages
        
    Returns:
        Scansion code: "=-" if starts with آ, "x" if ends with vowel+h, "=" otherwise
    """
    if trace is None:
        trace = []
    trace.append(f"L2S| INPUT_SUBSTRING: substr={word}")
    # Remove ھ and ں for scansion purposes
    word_no_aspirate = word.replace("\u06BE", "").replace("\u06BA", "")
    trace.append(f"L2S| AFTER_REMOVING_HAY_AND_NUN: result={word_no_aspirate}")
    word_no_diacritics = remove_araab(word_no_aspirate)
    
    code = "="
    if word[0] == '\u0622':  # آ
        code = "=-"
        trace.append("L2S| DETECTED_ALIF_MADD_START: return_code=-=")
        trace.append(f"L2S| PATTERN_MATCHED: starts_with_alif_madd,code={code}")
    elif len(word_no_diacritics) > 0 and is_vowel_plus_h(word_no_diacritics[-1]):
        code = "x"
        trace.append(f"L2S| DETECTED_VOWEL_PLUS_H_END: return_code=x")
        trace.append(f"L2S| PATTERN_MATCHED: ends_with_vowel_plus_h,code={code}")
    else:
        trace.append("L2S| DEFAULT_PATTERN: return_code==")
        trace.append(f"L2S| PATTERN_MATCHED: default_pattern,code={code}")
    
    return code


def length_three_scan(word: str, trace: Optional[List[str]] = None) -> str:
    """
    Handle 3-character words for scansion.
    
    Args:
        word: Three-character substring
        trace: Optional list to record trace messages
        
    Returns:
        Scansion code based on character patterns and diacritics
    """
    if trace is None:
        trace = []
    trace.append(f"L3S| INPUT_SUBSTRING: substr={word}")
    code = ""
    # Remove ھ and ں for scansion purposes
    word_no_aspirate = word.replace("\u06BE", "").replace("\u06BA", "")
    trace.append(f"L3S| AFTER_REMOVING_HAY_AND_NUN: result={word_no_aspirate}")
    word_no_diacritics = remove_araab(word_no_aspirate)
    trace.append(f"L3S| AFTER_REMOVING_ARAAB_STRIPPED: result={word_no_diacritics},length={len(word_no_diacritics)}")
    
    if len(word_no_diacritics) == 1:
        if word_no_diacritics[0] == 'آ':
            trace.append("L3S| STRIPPED_LENGTH_1_ALIF_MADD: return_code=-")
            return "-"
        else:
            trace.append("L3S| STRIPPED_LENGTH_1_NO_ALIF_MADD: return_code==")
            return "="
    elif len(word_no_diacritics) == 2:
        trace.append("L3S| STRIPPED_LENGTH_DELEGATE: length=2,delegate_to=L2S")
        return length_two_scan(word, trace=trace)
    
    if is_muarrab(word_no_aspirate):
        trace.append("L3S| WORD_IS_MUARRAB: has_diacritics=true")
        trace.append("L3S| ENTERING_MUARRAB_BRANCH: checking_diacritic_patterns")
        diacritic_positions = locate_araab(word_no_aspirate)
        trace.append(f"L3S| LOCATED_DIACRITICS: positions={len(diacritic_positions)},mask='{diacritic_positions}'")
        
        if len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazm
            trace.append(f"L3S| CHECKING_DIACRITIC_AT_POSITION: pos=1,diacritic=jazm,character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}'")
            trace.append("L3S| PATTERN_CHECK_1: jazm_at_pos_1=true")
            if word_no_diacritics[0] == 'آ':
                trace.append(f"L3S| CHECKING_SUB_CONDITION: first_char='{word_no_diacritics[0]}',is_alif_madd=true")
                code = "=--"
                trace.append(f"L3S| PATTERN_MATCHED: diacritic=jazm_at_pos_1,first_char_is_alif_madd=true,branch=if,code={code}")
            else:
                trace.append(f"L3S| CHECKING_SUB_CONDITION: first_char='{word_no_diacritics[0] if len(word_no_diacritics) > 0 else 'N/A'}',is_alif_madd=false")
                code = "=-"
                trace.append(f"L3S| PATTERN_MATCHED: diacritic=jazm_at_pos_1,first_char='{word_no_diacritics[0] if len(word_no_diacritics) > 0 else 'N/A'}',is_alif_madd=false,branch=else,ruled_out_patterns=[alif_madd],code={code}")
        elif len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                               diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                               diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
            diacritic_type = "zer" if diacritic_positions[1] == ARABIC_DIACRITICS[1] else ("zabar" if diacritic_positions[1] == ARABIC_DIACRITICS[8] else "paish")
            trace.append(f"L3S| CHECKING_DIACRITIC_AT_POSITION: pos=1,diacritic={diacritic_type},character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}'")
            trace.append(f"L3S| PATTERN_CHECK_2: {diacritic_type}_at_pos_1=true,ruled_out_patterns=[jazm]")
            code = "-="
            trace.append(f"L3S| PATTERN_MATCHED: diacritic={diacritic_type}_at_pos_1,ruled_out_patterns=[jazm],code={code}")
        elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[0]:  # shadd
            trace.append(f"L3S| CHECKING_DIACRITIC_AT_POSITION: pos=1,diacritic=shadd,character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}'")
            trace.append("L3S| PATTERN_CHECK_3: shadd_at_pos_1=true,ruled_out_patterns=[jazm,zer/zabar/paish]")
            code = "=="
            trace.append(f"L3S| PATTERN_MATCHED: diacritic=shadd_at_pos_1,ruled_out_patterns=[jazm,zer/zabar/paish],code={code}")
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=2,character='{word_no_diacritics[2]}'")
            trace.append("L3S| PATTERN_CHECK_4: alif_at_pos_2=true,ruled_out_patterns=[jazm,zer/zabar/paish,shadd]")
            code = "-="
            trace.append(f"L3S| PATTERN_MATCHED: alif_at_pos_2,ruled_out_patterns=[jazm,zer/zabar/paish,shadd],code={code}")
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] in ['ا', 'ی', 'ے', 'و', 'ہ']:  # vowels at end
            vowel_char = word_no_diacritics[2]
            trace.append(f"L3S| CHECKING_VOWEL_AT_POSITION: pos=2,character='{vowel_char}'")
            trace.append(f"L3S| PATTERN_CHECK_5: vowel_at_pos_2='{vowel_char}',ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2]")
            if word_no_diacritics[1] == 'ا':
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_1_character='{word_no_diacritics[1]}',is_alif=true")
                code = "=-"
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_pos_2='{vowel_char}',alif_at_pos_1=true,branch=if,code={code}")
            else:
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_1_character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}',is_alif=false")
                code = "-="
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_pos_2='{vowel_char}',alif_at_pos_1=false,branch=else,code={code}")
        elif (len(word_no_diacritics) > 1 and word_no_diacritics[1] in ['ا', 'ی', 'ے', 'و']) or (len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ہ'):  # vowels at center
            vowel_pos = None
            vowel_char = None
            if len(word_no_diacritics) > 1 and word_no_diacritics[1] in ['ا', 'ی', 'ے', 'و']:
                vowel_pos = 1
                vowel_char = word_no_diacritics[1]
            elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ہ':
                vowel_pos = 2
                vowel_char = 'ہ'
            trace.append(f"L3S| CHECKING_VOWEL_AT_POSITION: pos={vowel_pos},character='{vowel_char}'")
            trace.append(f"L3S| PATTERN_CHECK_6: vowel_at_pos_{vowel_pos}=true,ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2,vowel_at_pos_2]")
            code = "=-"
            trace.append(f"L3S| PATTERN_MATCHED: vowel_at_pos_{vowel_pos}='{vowel_char}',ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2,vowel_at_pos_2],code={code}")
        else:  # default case
            trace.append("L3S| PATTERN_CHECK_7: all_previous_checks_failed")
            trace.append("L3S| NO_PATTERN_MATCHED: using_default_muarrab_rule")
            code = "=-"
            trace.append(f"L3S| PATTERN_MATCHED: default_muarrab,ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2,vowel_at_pos_2,vowel_at_center],code={code}")
    else:
        trace.append("L3S| WORD_NOT_MUARRAB: has_diacritics=false")
        trace.append("L3S| ENTERING_NON_MUARRAB_BRANCH: checking_character_patterns")
        if word_no_diacritics[0] == 'آ':
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=0,character='{word_no_diacritics[0]}'")
            trace.append("L3S| PATTERN_CHECK_1: starts_with_alif_madd=true")
            code = "=="
            trace.append(f"L3S| PATTERN_MATCHED: starts_with_alif_madd_at_pos_0,code={code}")
        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':  # Alif at centre
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=1,character='{word_no_diacritics[1]}'")
            trace.append("L3S| PATTERN_CHECK_2: alif_at_pos_1=true,ruled_out_patterns=[alif_madd_at_pos_0]")
            code = "=-"
            trace.append(f"L3S| PATTERN_MATCHED: alif_at_pos_1,ruled_out_patterns=[alif_madd_at_pos_0],code={code}")
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=2,character='{word_no_diacritics[2]}'")
            trace.append("L3S| PATTERN_CHECK_3: alif_at_pos_2=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1]")
            code = "-="
            trace.append(f"L3S| PATTERN_MATCHED: alif_at_pos_2,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1],code={code}")
        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] in ['ی', 'ے', 'و', 'ہ']:  # vowels + h at centre
            trace.append(f"L3S| PATTERN_CHECK_4: vowel_at_center=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2]")
            if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ہ':
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_2_character='{word_no_diacritics[2]}',is_haa=true")
                code = "=-"
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_center,haa_at_end=true,branch=if,code={code}")
            elif len(word_no_diacritics) > 2 and word_no_diacritics[2] in ['ی', 'ے', 'و']:  # vowels + h at end
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_2_character='{word_no_diacritics[2]}',is_vowel=true")
                code = "-="
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_center,vowel_at_end=true,branch=elif,code={code}")
            else:
                trace.append("L3S| CHECKING_SUB_CONDITION: pos_2_check=false,using_else_branch")
                code = "=-"
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_center,no_special_end,branch=else,code={code}")
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] in ['ی', 'ے', 'و', 'ہ']:  # vowels + h at end
            trace.append("L3S| PATTERN_CHECK_5: vowel_at_end=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center]")
            code = "-="
            trace.append(f"L3S| PATTERN_MATCHED: vowel_at_end,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center],code={code}")
        elif len(word_no_diacritics) > 0 and is_vowel_plus_h(word_no_diacritics[0]):
            trace.append(f"L3S| PATTERN_CHECK_6: vowel_plus_h_at_start=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center,vowel_at_end]")
            code = "-="
            trace.append(f"L3S| PATTERN_MATCHED: vowel_plus_h_at_start,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center,vowel_at_end],code={code}")
        else:
            trace.append("L3S| PATTERN_CHECK_7: all_previous_checks_failed")
            code = "-="
            trace.append(f"L3S| PATTERN_MATCHED: default_non_muarrab,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center,vowel_at_end,vowel_plus_h_at_start],code={code}")
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(word_no_diacritics):
        old_code = code
        code = noon_ghunna(word, code)
        if old_code != code:
            trace.append(f"L3S| APPLIED_NOON_GHUNNA_ADJUSTMENT: old_code={old_code},new_code={code}")
    
    trace.append(f"L3S| RETURNING: code={code}")
    return code


def length_four_scan(word: str, trace: Optional[List[str]] = None) -> str:
    """
    Handle 4-character words for scansion.
    
    Args:
        word: Four-character substring
        
    Returns:
        Scansion code based on character patterns
    """
    if trace is None:
        trace = []
    code = ""
    # Remove ھ and ں for scansion purposes
    word_no_aspirate = word.replace("\u06BE", "").replace("\u06BA", "")
    word_no_diacritics = remove_araab(word_no_aspirate)
    
    if len(word_no_diacritics) == 1:
        trace.append("L4S| STRIPPED_LENGTH_DELEGATE: length=1,delegate_to=L1S")
        code = length_one_scan(word_no_aspirate, trace=trace)
    elif len(word_no_diacritics) == 2:
        trace.append("L4S| STRIPPED_LENGTH_DELEGATE: length=2,delegate_to=L2S")
        code = length_two_scan(word_no_aspirate, trace=trace)
    elif len(word_no_diacritics) == 3:
        trace.append("L4S| STRIPPED_LENGTH_DELEGATE: length=3,delegate_to=L3S")
        code = length_three_scan(word_no_aspirate, trace=trace)
    else:
        if word_no_diacritics[0] == 'آ':
            # Remove first character and scan the rest
            remaining = word_no_aspirate[1:] if len(word_no_aspirate) > 1 else ""
            trace.append(f"L4S| SPLIT_AT_POSITION: split_pos=1,delegate_to=L3S,remaining={remaining}")
            code = "=" + length_three_scan(remaining, trace=trace)
        elif is_muarrab(word_no_aspirate):
            trace.append("L4S| WORD_IS_MUARRAB: has_diacritics=true")
            diacritic_positions = locate_araab(word_no_aspirate)
            if len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':
                if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                    code = "=--"
                else:
                    code = "=="
            elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                code = "-=-"
            else:
                if len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'و':
                    if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ت' and len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazm
                        code = "=-"
                    else:
                        if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            code = "-=-"
                        else:
                            if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "=--"
                            else:
                                code = "=="
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ی':
                    if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ت' and len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazm
                        code = "=-"
                    elif len(diacritic_positions) > 0 and (diacritic_positions[0] == ARABIC_DIACRITICS[1] or  # zer
                                           diacritic_positions[0] == ARABIC_DIACRITICS[8] or  # zabar
                                           diacritic_positions[0] == ARABIC_DIACRITICS[9]):  # paish
                        if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            code = "-=-"
                        else:
                            if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "=--"
                            else:
                                code = "=="
                    else:
                        code = "=="
                else:
                    if len(diacritic_positions) > 0 and (diacritic_positions[0] == ARABIC_DIACRITICS[1] or  # zer
                                        diacritic_positions[0] == ARABIC_DIACRITICS[8] or  # zabar
                                        diacritic_positions[0] == ARABIC_DIACRITICS[9]):  # paish
                        if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            if len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                                code = "-=-"
                            elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "-=-"
                            else:
                                code = "--="
                        elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "=="
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=-"
                        else:
                            if len(word_no_diacritics) > 3 and (word_no_diacritics[3] == 'ا' or word_no_diacritics[3] == 'ی'):
                                code = "--="
                            else:
                                code = "-=-"
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "=="
                        else:
                            code = "=--"
                    elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "-=-"
                    elif len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                          diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                          diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                        code = "=="
                    elif len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                        code = "-=-"
                    else:
                        code = "=="
        elif len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
            if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ا':
                code = "=="
            elif len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                code = "=="
            else:
                code = "-=-"
        else:  # default
            code = "=="
            trace.append("L4S| PATTERN_MATCHED: default_non_muarrab,code====")
        trace.append(f"L4S| PATTERN_MATCHED: pattern=non_muarrab_vowel_check,code={code}")
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(word_no_diacritics):
        old_code = code
        code = noon_ghunna(word, code)
        if old_code != code:
            trace.append(f"L4S| APPLIED_NOON_GHUNNA_ADJUSTMENT: old_code={old_code},new_code={code}")
    
    trace.append(f"L4S| RETURNING: code={code}")
    return code


def length_five_scan(word: str, trace: Optional[List[str]] = None) -> str:
    """
    Handle 5+ character words for scansion.
    
    Args:
        word: Five or more character substring
        trace: Optional list to record trace messages
        
    Returns:
        Scansion code based on character patterns
    """
    if trace is None:
        trace = []
    trace.append(f"L5S| INPUT_SUBSTRING: substr={word}")
    logger.debug(f"length_five_scan: Input substring = '{word}'")
    code = ""
    # Remove ھ and ں for scansion purposes
    word_no_aspirate = word.replace("\u06BE", "").replace("\u06BA", "")
    trace.append(f"L5S| AFTER_REMOVING_HAY_AND_NUN: result={word_no_aspirate}")
    logger.debug(f"length_five_scan: After removing ھ and ں = '{word_no_aspirate}'")
    word_no_diacritics = remove_araab(word_no_aspirate)
    trace.append(f"L5S| AFTER_REMOVING_ARAAB_STRIPPED: result={word_no_diacritics},length={len(word_no_diacritics)}")
    logger.debug(f"length_five_scan: After removing araab (word_no_diacritics) = '{word_no_diacritics}' (length={len(word_no_diacritics)})")
    
    # --- FIX: aspirated + ی should force short medial vowel (e.g. اندھیرے) ---
    if 'ھ' in word:
        for i in range(len(word) - 2):
            if word[i+1] == 'ھ' and word[i+2] == 'ی':
                trace.append(f"L5S| DETECTED_ASPIRATED_YEH_PATTERN: start_pos={i+1},end_pos={i+2}")
                trace.append("L5S| EARLY_RETURN_ASPIRATED_YEH_PATTERN: return_code=-==")
                logger.debug(f"length_five_scan: Early return for aspirated+ی pattern, returning '-=='")
                return "-=="    
    if len(word_no_diacritics) == 3:
        trace.append("L5S| STRIPPED_LENGTH_DELEGATE: length=3,delegate_to=L3S")
        logger.debug(f"length_five_scan: Stripped length is 3, delegating to length_three_scan")
        code = length_three_scan(word, trace=trace)
    elif len(word_no_diacritics) == 4:
        trace.append("L5S| STRIPPED_LENGTH_DELEGATE: length=4,delegate_to=L4S")
        logger.debug(f"length_five_scan: Stripped length is 4, delegating to length_four_scan")
        code = length_four_scan(word, trace=trace)
    else:
        if word_no_diacritics[0] == 'آ':
            # Remove first 2 characters (آ + next) and scan the rest
            remaining = word_no_aspirate[2:] if len(word_no_aspirate) > 2 else ""
            trace.append(f"L5S| SPLIT_AT_POSITION: split_pos=2,delegate_to=L4S,remaining={remaining}")
            logger.debug(f"length_five_scan: Split at position 2 (آ pattern): prefix='{word_no_aspirate[:2]}', remaining='{remaining}'")
            code = "=" + length_four_scan(remaining, trace=trace)
        elif is_muarrab(word_no_aspirate):
            trace.append("L5S| WORD_IS_MUARRAB: has_diacritics=true")
            logger.debug(f"length_five_scan: Word is muarrab (has diacritics), using muarrab path")
            diacritic_positions = locate_araab(word_no_aspirate)
            if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'ا' or word_no_diacritics[2] == 'ا' or word_no_diacritics[3] == 'ا'):  # check alif at position 2,3,4
                trace.append("L5S| MUARRAB_PATH_ALIF_DETECTED: checking_positions_2_3_4")
                # Position 3 Alif
                if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                    trace.append("L5S| ALIF_POSITION_DETECTED: position=3")
                    # If alif is followed by hamza/ye ending, final syllable is ambiguous
                    if 'ئ' in word_no_diacritics[3:] or word_no_diacritics.endswith('ے'):
                        code = "-=x"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_3_with_hamza_ye_ending,code={code}")
                        logger.debug(f"length_five_scan: Position 3 Alif with hamza/ye ending: code='{code}'")
                    else:
                        code = "-=="
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_3_default,code={code}")
                        logger.debug(f"length_five_scan: Position 3 Alif: code='{code}'")
                # Position 2 Alif
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':
                    trace.append("L5S| ALIF_POSITION_DETECTED: position=2")
                    if len(diacritic_positions) > 0 and is_muarrab(diacritic_positions[0]):
                        if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                            split_pos = 3
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=alif_at_pos_2_muarrab_0_and_1,remaining={remaining}")
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, muarrab[0] and muarrab[1]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining, trace=trace)
                        else:
                            split_pos = 4
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=alif_at_pos_2_muarrab_0_only,remaining={remaining}")
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, muarrab[0] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining, trace=trace)
                    else:
                        if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                            split_pos = 2
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=alif_at_pos_2_muarrab_1_only,remaining={remaining}")
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, muarrab[1] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining, trace=trace)
                        else:
                            split_pos = 3
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=alif_at_pos_2_no_muarrab,remaining={remaining}")
                            logger.debug(f"length_five_scan: Split at position {split_pos} (Position 2 Alif, no muarrab): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining, trace=trace)
                # Position 4 Alif
                else:
                    trace.append("L5S| ALIF_POSITION_DETECTED: position=4")
                    code = "==-"
                    if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                         diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                        code = "--=-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_diacritic_zer_zabar_paish_at_1,code={code}")
                        logger.debug(f"length_five_scan: Position 4 Alif with zer/zabar/paish at diacritic_positions[1]: code='{code}'")
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "--=-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_diacritic_jazr_at_1,code={code}")
                        logger.debug(f"length_five_scan: Position 4 Alif with jazr at diacritic_positions[1]: code='{code}'")
                    elif len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                        trace.append("L5S| CHECKING_CHARACTER_PATTERN: first_char=ب")
                        if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_with_vowel_at_1,code={code}")
                        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_ر,code={code}")
                        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_ن,code={code}")
                        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_غ,code={code}")
                        else:
                            code = "--=-"
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_default,code={code}")
                    else:
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_default,code={code}")
            else:
                if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'و' or word_no_diacritics[2] == 'و' or word_no_diacritics[3] == 'و' or
                                         word_no_diacritics[1] == 'ی' or word_no_diacritics[2] == 'ی' or word_no_diacritics[3] == 'ی'):
                    trace.append("L5S| MUARRAB_PATH_VOWEL_DETECTED: و/ی_at_positions_1_2_3")
                    if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'و' or word_no_diacritics[1] == 'ی'):
                        trace.append(f"L5S| VOWEL_POSITION_DETECTED: position=1,char={word_no_diacritics[1]}")
                        if len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                            trace.append("L5S| DIACRITIC_DETECTED: diacritic=jazr_at_pos_1")
                            if len(diacritic_positions) > 0 and is_muarrab(diacritic_positions[0]):
                                if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                                    split_pos = 5
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_jazr_muarrab_0_and_1,remaining={remaining}")
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, muarrab[0] and muarrab[1]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining, trace=trace)
                                else:
                                    split_pos = 4
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_jazr_muarrab_0_only,remaining={remaining}")
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, muarrab[0] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining, trace=trace)
                            else:
                                if len(diacritic_positions) > 1 and is_muarrab(diacritic_positions[1]):
                                    split_pos = 3
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_jazr_muarrab_1_only,remaining={remaining}")
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, muarrab[1] only): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining, trace=trace)
                                else:
                                    split_pos = 4
                                    remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                    trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_jazr_no_muarrab,remaining={remaining}")
                                    logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr, no muarrab): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                    code = "=" + length_three_scan(remaining, trace=trace)
                        elif len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                               diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                               diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            trace.append("L5S| DIACRITIC_DETECTED: diacritic=zer_zabar_paish_at_pos_1")
                            if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                                code = "--=-"
                                trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_zer_zabar_paish_at_1_and_2,code={code}")
                            else:
                                code = "-=="
                                trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_zer_zabar_paish_at_1_only,code={code}")
                        else:
                            trace.append("L5S| DIACRITIC_DETECTED: diacritic=other_at_pos_1")
                            if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                                 diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                                trace.append("L5S| DIACRITIC_DETECTED: diacritic=zer_zabar_paish_at_pos_2")
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "=-="
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_zer_zabar_paish_at_2_and_3,code={code}")
                                elif len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazr
                                    code = "==-"
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_zer_zabar_paish_at_2_jazr_at_3,code={code}")
                                else:
                                    code = "==-"
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_zer_zabar_paish_at_2_default,code={code}")
                            elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                trace.append("L5S| DIACRITIC_DETECTED: diacritic=jazr_at_pos_2")
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "=-="
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_jazr_at_2_zer_zabar_paish_at_3,code={code}")
                                elif len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazr
                                    code = "=---"
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_1_jazr_at_2_and_3,code={code}")
                                else:
                                    if len(diacritic_positions) > 2 and is_muarrab(diacritic_positions[2]):
                                        split_pos = 4
                                        remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                        trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_jazr_at_2_muarrab_2,remaining={remaining}")
                                        logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr at 2, muarrab[2]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                        code = "=" + length_three_scan(remaining, trace=trace)
                                    else:
                                        split_pos = 3
                                        remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                        trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_jazr_at_2_no_muarrab_2,remaining={remaining}")
                                        logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, jazr at 2, no muarrab[2]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                        code = "=" + length_three_scan(remaining, trace=trace)
                            else:
                                split_pos = 2
                                remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                                trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=و/ی_at_pos_1_no_jazr_at_2,remaining={remaining}")
                                logger.debug(f"length_five_scan: Split at position {split_pos} (Position 1 و/ی, no jazr at 2): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                                code = "=" + length_three_scan(remaining, trace=trace)
                    elif len(word_no_diacritics) > 2 and (word_no_diacritics[2] == 'و' or word_no_diacritics[2] == 'ی'):
                        trace.append(f"L5S| VOWEL_POSITION_DETECTED: position=2,char={word_no_diacritics[2]}")
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            trace.append("L5S| DIACRITIC_DETECTED: diacritic=zer_zabar_paish_at_pos_2")
                            if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                                diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "-----"  # highly unlikely
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_2_zer_zabar_paish_at_1_2_3,code={code}")
                                else:
                                    code = "--=-"
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_2_zer_zabar_paish_at_1_and_2,code={code}")
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                            trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_2_jazr_at_2,code={code}")
                        else:
                            code = "-=="
                            trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_2_default,code={code}")
                    elif len(word_no_diacritics) > 3 and (word_no_diacritics[3] == 'و' or word_no_diacritics[3] == 'ی'):
                        trace.append(f"L5S| VOWEL_POSITION_DETECTED: position=3,char={word_no_diacritics[3]}")
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            trace.append("L5S| DIACRITIC_DETECTED: diacritic=zer_zabar_paish_at_pos_2")
                            if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                                diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "---="  # highly unlikely
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_3_zer_zabar_paish_at_1_2_3,code={code}")
                                else:
                                    code = "--=-"
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_3_zer_zabar_paish_at_1_and_2,code={code}")
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                            trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_3_jazr_at_2,code={code}")
                        else:
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: و/ی_at_pos_3_default,code={code}")
                    else:
                        trace.append("L5S| VOWEL_POSITION_DETECTED: position=other")
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                             diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                             diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            trace.append("L5S| DIACRITIC_DETECTED: diacritic=zer_zabar_paish_at_pos_2")
                            if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                                diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                                diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                                if len(diacritic_positions) > 3 and (diacritic_positions[3] == ARABIC_DIACRITICS[1] or  # zer
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[8] or  # zabar
                                                     diacritic_positions[3] == ARABIC_DIACRITICS[9]):  # paish
                                    code = "-----"  # highly unlikely
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_other_zer_zabar_paish_at_1_2_3,code={code}")
                                else:
                                    code = "--=-"
                                    trace.append(f"L5S| PATTERN_MATCHED: و/ی_other_zer_zabar_paish_at_1_and_2,code={code}")
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                            trace.append(f"L5S| PATTERN_MATCHED: و/ی_other_jazr_at_2,code={code}")
                        else:
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: و/ی_other_default,code={code}")
                else:
                    trace.append("L5S| MUARRAB_PATH_NO_VOWEL: checking_diacritics_only")
                    if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                         diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                        trace.append("L5S| DIACRITIC_DETECTED: diacritic=zer_zabar_paish_at_pos_1")
                        if len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                            if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ا':
                                code = "---="
                                trace.append(f"L5S| PATTERN_MATCHED: no_vowel_zer_zabar_paish_at_1_and_2_alif_at_4,code={code}")
                            else:
                                code = "--=-"
                                trace.append(f"L5S| PATTERN_MATCHED: no_vowel_zer_zabar_paish_at_1_and_2,code={code}")
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=="
                            trace.append(f"L5S| PATTERN_MATCHED: no_vowel_zer_zabar_paish_at_1_jazr_at_2,code={code}")
                        else:
                            code = "-=="
                            trace.append(f"L5S| PATTERN_MATCHED: no_vowel_zer_zabar_paish_at_1_default,code={code}")
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        trace.append("L5S| DIACRITIC_DETECTED: diacritic=jazr_at_pos_1")
                        if len(diacritic_positions) > 0 and is_muarrab(diacritic_positions[0]):
                            split_pos = 4
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=no_vowel_jazr_at_1_muarrab_0,remaining={remaining}")
                            logger.debug(f"length_five_scan: Split at position {split_pos} (no و/ی, jazr at 1, muarrab[0]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining, trace=trace)
                        else:
                            split_pos = 3
                            remaining = word_no_aspirate[split_pos:] if len(word_no_aspirate) > split_pos else ""
                            trace.append(f"L5S| SPLIT_DECISION: split_pos={split_pos},reason=no_vowel_jazr_at_1_no_muarrab_0,remaining={remaining}")
                            logger.debug(f"length_five_scan: Split at position {split_pos} (no و/ی, jazr at 1, no muarrab[0]): prefix='{word_no_aspirate[:split_pos]}', remaining='{remaining}'")
                            code = "=" + length_three_scan(remaining, trace=trace)
                    elif len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                          diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                          diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                        code = "=-="
                        trace.append(f"L5S| PATTERN_MATCHED: no_vowel_zer_zabar_paish_at_2,code={code}")
                    # else: empty code (no change)
        elif len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'ا' or word_no_diacritics[2] == 'ا' or word_no_diacritics[3] == 'ا'):  # check alif at position 2,3,4
            trace.append("L5S| NON_MUARRAB_PATH_ALIF_DETECTED: checking_positions_2_3_4")
            logger.debug(f"length_five_scan: Non-muarrab path with alif at position 2,3, or 4")
            # Position 3 Alif
            if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                trace.append("L5S| ALIF_POSITION_DETECTED: position=3_non_muarrab")
                code = "-=="
                trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_3_non_muarrab,code={code}")
                logger.debug(f"length_five_scan: Position 3 Alif (non-muarrab): code='{code}' (no split)")
            # Position 2 Alif
            elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':
                trace.append("L5S| ALIF_POSITION_DETECTED: position=2_non_muarrab")
                logger.debug(f"length_five_scan: Position 2 Alif (non-muarrab): checking patterns")
                if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ا':
                    code = "==-"
                    trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_2_and_3_non_muarrab,code={code}")
                    logger.debug(f"length_five_scan: Position 2 Alif with alif at 3: code='{code}' (no split)")
                else:
                    if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                        if len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                            code = "=-="
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_2_vowels_at_3_and_4_non_muarrab,code={code}")
                            logger.debug(f"length_five_scan: Position 2 Alif with vowels at 3 and 4: code='{code}' (no split)")
                        else:
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_2_vowel_at_3_non_muarrab,code={code}")
                            logger.debug(f"length_five_scan: Position 2 Alif with vowel at 3: code='{code}' (no split)")
                    elif len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                        code = "=-="
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_2_vowel_at_4_non_muarrab,code={code}")
                        logger.debug(f"length_five_scan: Position 2 Alif with vowel at 4: code='{code}' (no split)")
                    else:
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_2_default_non_muarrab,code={code}")
                        logger.debug(f"length_five_scan: Position 2 Alif (default): code='{code}' (no split)")
            # Position 4 Alif
            else:
                trace.append("L5S| ALIF_POSITION_DETECTED: position=4_non_muarrab")
                code = "==-"
                logger.debug(f"length_five_scan: Position 4 Alif (non-muarrab): initial code='{code}'")
                if len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                    trace.append("L5S| CHECKING_CHARACTER_PATTERN: first_char=ب_non_muarrab")
                    if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_with_vowel_at_1_non_muarrab,code={code}")
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_ر_non_muarrab,code={code}")
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_ن_non_muarrab,code={code}")
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_غ_non_muarrab,code={code}")
                    else:
                        code = "--=-"
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_ب_default_non_muarrab,code={code}")
                    logger.debug(f"length_five_scan: Position 4 Alif with 'ب' at start: code='{code}' (no split)")
                else:
                    trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_default_non_muarrab,code={code}")
        elif len(word_no_diacritics) > 1 and (is_vowel_plus_h(word_no_diacritics[1]) or is_vowel_plus_h(word_no_diacritics[2]) or is_vowel_plus_h(word_no_diacritics[3])):  # check vowels at position 2,3,4
            trace.append("L5S| NON_MUARRAB_PATH_VOWEL_DETECTED: checking_positions_2_3_4")
            logger.debug(f"length_five_scan: Non-muarrab path with vowels at position 2,3, or 4")
            # Position 3 Vowel
            if len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                trace.append(f"L5S| VOWEL_POSITION_DETECTED: position=3_non_muarrab,char={word_no_diacritics[2]}")
                code = "-=="
                if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                    code = "-=="
                    trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_3_and_4_non_muarrab,code={code}")
                else:
                    trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_3_non_muarrab,code={code}")
                logger.debug(f"length_five_scan: Position 3 Vowel: code='{code}' (no split)")
            # Position 2 Vowel
            elif len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                trace.append(f"L5S| VOWEL_POSITION_DETECTED: position=2_non_muarrab,char={word_no_diacritics[1]}")
                if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                    code = "==-"
                    trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_2_and_3_non_muarrab,code={code}")
                    logger.debug(f"length_five_scan: Position 2 Vowel with vowel at 3: code='{code}' (no split)")
                else:
                    if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                        if len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                            code = "=-="
                            trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_2_3_and_4_non_muarrab,code={code}")
                            logger.debug(f"length_five_scan: Position 2 Vowel with vowels at 3 and 4: code='{code}' (no split)")
                        else:
                            code = "==-"
                            trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_2_and_3_non_muarrab,code={code}")
                            logger.debug(f"length_five_scan: Position 2 Vowel with vowel at 3: code='{code}' (no split)")
                    elif len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                        code = "=-="
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_2_and_4_non_muarrab,code={code}")
                        logger.debug(f"length_five_scan: Position 2 Vowel with vowel at 4: code='{code}' (no split)")
                    else:
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_2_default_non_muarrab,code={code}")
                        logger.debug(f"length_five_scan: Position 2 Vowel (default): code='{code}' (no split)")
            # Position 4 Vowel
            else:
                trace.append("L5S| VOWEL_POSITION_DETECTED: position=4_non_muarrab")
                code = "==-"
                if len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                    trace.append("L5S| CHECKING_CHARACTER_PATTERN: first_char=ب_vowel_path")
                    if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_4_ب_with_vowel_at_1_non_muarrab,code={code}")
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_4_ب_ر_non_muarrab,code={code}")
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_4_ب_ن_non_muarrab,code={code}")
                    elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                        code = "==-"
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_4_ب_غ_non_muarrab,code={code}")
                    else:
                        code = "--=-"
                        trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_4_ب_default_non_muarrab,code={code}")
                if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ت' and len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ی':
                    old_code = code
                    code = code[:-1] + "="
                    trace.append(f"L5S| APPLIED_YAA_TAA_ADJUSTMENT: old_code={old_code},new_code={code}")
                else:
                    trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_4_default_non_muarrab,code={code}")
                logger.debug(f"length_five_scan: Position 4 Vowel: code='{code}' (no split)")
        else:  # consonants
            trace.append("L5S| NON_MUARRAB_PATH_CONSONANTS_ONLY: no_alif_no_vowel")
            logger.debug(f"length_five_scan: Non-muarrab path - consonants only")
            code = "==-"
            if len(word_no_diacritics) > 0 and word_no_diacritics[0] == 'ب':
                trace.append("L5S| CHECKING_CHARACTER_PATTERN: first_char=ب_consonants")
                if len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                    code = "==-"
                    trace.append(f"L5S| PATTERN_MATCHED: consonants_ب_with_vowel_at_1,code={code}")
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ر':
                    code = "==-"
                    trace.append(f"L5S| PATTERN_MATCHED: consonants_ب_ر,code={code}")
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ن':
                    code = "==-"
                    trace.append(f"L5S| PATTERN_MATCHED: consonants_ب_ن,code={code}")
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'غ':
                    code = "==-"
                    trace.append(f"L5S| PATTERN_MATCHED: consonants_ب_غ,code={code}")
                else:
                    code = "--=-"
                    trace.append(f"L5S| PATTERN_MATCHED: consonants_ب_default,code={code}")
            if len(word_no_diacritics) > 0 and (word_no_diacritics[0] == 'ت' or word_no_diacritics[0] == 'ش'):
                code = "-=="
                trace.append(f"L5S| PATTERN_MATCHED: consonants_first_char_ت_or_ش,code={code}")
            if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ت' and len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ی':
                old_code = code
                code = code[:-1] + "="
                trace.append(f"L5S| APPLIED_YAA_TAA_ADJUSTMENT: old_code={old_code},new_code={code}")
            if len(word_no_diacritics) > 4 and word_no_diacritics[4] == 'ا':
                code = "-=="
                trace.append(f"L5S| PATTERN_MATCHED: consonants_alif_at_pos_4,code={code}")
            elif len(word_no_diacritics) > 4 and is_vowel_plus_h(word_no_diacritics[4]):
                code = "=-="
                trace.append(f"L5S| PATTERN_MATCHED: consonants_vowel_at_pos_4,code={code}")
            else:
                trace.append(f"L5S| PATTERN_MATCHED: consonants_default,code={code}")
            logger.debug(f"length_five_scan: Consonants path: code='{code}' (no split)")
    
    # Apply noon ghunna adjustments if needed
    if contains_noon(word_no_diacritics):
        old_code = code
        code = noon_ghunna(word, code)
        if old_code != code:
            trace.append(f"L5S| APPLIED_NOON_GHUNNA_ADJUSTMENT: old_code={old_code},new_code={code}")
            logger.debug(f"length_five_scan: Applied noon ghunna adjustment: '{old_code}' -> '{code}'")

    # Apply yaa adjustment if needed
    if code.endswith("==") and word_no_diacritics.endswith("ے"):
        new_code = code[:-1] + "x"
        trace.append(f"L5S| APPLIED_YAA_ADJUSTMENT: old_code={code},new_code={new_code}")
        logger.debug(f"length_five_scan: Applying yaa adjustment: '{code}' -> '{new_code}'")
        code = new_code

    trace.append(f"L5S| RETURNING: code={code}")
    logger.debug(f"length_five_scan: Final code for '{word}' = '{code}'")
    return code
