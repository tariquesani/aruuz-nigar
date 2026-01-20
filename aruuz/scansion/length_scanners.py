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
    
    # ============================================================================
    # PATTERN MATCHING: Single-character word scansion
    # ============================================================================
    # Priority order (checked in sequence, first match wins):
    # 1. Alif Madd (آ) - special long character
    # 2. Default - all other characters are short
    # ============================================================================
    
    # Pattern 1: Alif Madd (آ)
    # Linguistic rule: Alif Madd (آ) is a special long character representing
    #                  a long vowel sound (alif maddah).
    # Justification: Alif Madd gets long weight (=) because it represents
    #                a long vowel sound. This is the only single character
    #                that gets long weight in standalone context.
    if word_no_diacritics == "آ":
        trace.append("L1S| DETECTED_ALIF_MADD: return_code==")
        return "="  # Long: Alif Madd represents a long vowel sound
    
    # Pattern 2: Default pattern (all other characters)
    # Linguistic rule: All single characters except Alif Madd are treated as short.
    # Justification: Single characters default to short weight (-) unless they
    #                are the special Alif Madd character. This is the fallback
    #                pattern for all other single-character words.
    else:
        trace.append("L1S| NO_ALIF_MADD: return_code=-")
        return "-"  # Short: Default for all non-Alif-Madd single characters


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
    
    # ============================================================================
    # PATTERN MATCHING: Two-character word scansion
    # ============================================================================
    # Priority order (checked in sequence, first match wins):
    # 1. Alif Madd (آ) at start - special long character, splittable
    # 2. Vowel plus h at end - flexible terminal pattern
    # 3. Default - single long syllable
    # ============================================================================
    
    # Default case: Single long syllable
    # Justification: Two-character words default to a single long syllable (=)
    #                unless they match a specific pattern that requires different treatment.
    code = "="
    
    # Pattern 1: Alif Madd (آ) at start
    # Linguistic rule: Alif Madd (آ) is a special long character that creates
    #                  a splittable long-short pattern.
    # Justification: Alif Madd at start creates long-short pattern ("=-").
    #                The آ itself is long, and it splits the word into two syllables.
    #                This is the highest priority pattern for two-character words.
    if word[0] == '\u0622':  # آ
        code = "=-"  # Long-short: Alif Madd (long) + remaining character (short)
        trace.append("L2S| DETECTED_ALIF_MADD_START: return_code==-")
        trace.append(f"L2S| PATTERN_MATCHED: starts_with_alif_madd,code={code}")
    
    # Pattern 2: Vowel plus h at end (flexible terminal)
    # Linguistic rule: Words ending in vowel plus h (ا،ی،ے،و،ہ) are treated as flexible.
    #                  The flexible terminal allows the word to be either long or short
    #                  depending on metrical context.
    # Justification: Flexible terminals get code "x" to indicate they can be either
    #                long (=) or short (-) depending on the metrical requirements.
    #                This flexibility is essential for proper scansion matching.
    elif len(word_no_diacritics) > 0 and is_vowel_plus_h(word_no_diacritics[-1]):
        code = "x"  # Flexible: Can be either long (=) or short (-) based on context
        trace.append(f"L2S| DETECTED_VOWEL_PLUS_H_END: return_code=x")
        trace.append(f"L2S| PATTERN_MATCHED: ends_with_vowel_plus_h,code={code}")
    
    # Pattern 3: Default pattern
    # Justification: When no specific pattern matches, use default single long syllable.
    #                This is the fallback for two-character words that don't match
    #                the special patterns above.
    else:
        trace.append("L2S| DEFAULT_PATTERN: return_code==")
        trace.append(f"L2S| PATTERN_MATCHED: default_pattern,code={code}")
    
    return code


def _has_vowel_at_center(word_no_diacritics: str) -> bool:
    """
    Check if word has a vowel at center position (position 1 or position 2 with 'ہ').
    
    This helper extracts the complex boolean condition for readability.
    Pattern: vowel at position 1 (ا, ی, ے, و) OR 'ہ' at position 2.
    
    Args:
        word_no_diacritics: Word with diacritics removed
        
    Returns:
        True if vowel found at center position
    """
    return (len(word_no_diacritics) > 1 and word_no_diacritics[1] in ['ا', 'ی', 'ے', 'و']) or (len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ہ')


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
    
    # ============================================================================
    # SECTION 1: EARLY EXITS - Length-based delegation
    # ============================================================================
    # These patterns handle cases where the word collapses to fewer characters
    # after removing diacritics and aspirates. These are checked FIRST because
    # they represent degenerate cases that need special handling.
    
    # Pattern: Word collapses to single character after stripping
    # Justification: When a multi-character word collapses to one phonetic unit,
    #                syllabic weight is inverted due to internal prosodic compensation.
    #                This is NOT equivalent to a standalone single-character word.
    #                Alif Madd (آ) gets short weight (-) in this context, others get long (=).
    if len(word_no_diacritics) == 1:
        if word_no_diacritics[0] == 'آ':
            trace.append("L3S| STRIPPED_LENGTH_1_ALIF_MADD: return_code=-")
            return "-"  # Short: Alif Madd in collapsed context becomes short
        else:
            trace.append("L3S| STRIPPED_LENGTH_1_NO_ALIF_MADD: return_code==")
            return "="  # Long: Other single characters get long weight
    
    # Pattern: Word collapses to two characters after stripping
    # Justification: Delegate to length_two_scan which has specialized logic
    #                for two-character patterns (flexible terminals, alif madd, etc.)
    elif len(word_no_diacritics) == 2:
        trace.append("L3S| STRIPPED_LENGTH_DELEGATE: length=2,delegate_to=L2S")
        return length_two_scan(word, trace=trace)
    
    # ============================================================================
    # SECTION 2: PRIMARY SPLIT - Muarrab vs Non-Muarrab
    # ============================================================================
    # The fundamental division: words WITH diacritics (muarrab) vs WITHOUT.
    # Muarrab words use diacritic-driven pattern matching (more specific).
    # Non-muarrab words use character-driven pattern matching (less specific).
    
    if is_muarrab(word_no_aspirate):
        trace.append("L3S| WORD_IS_MUARRAB: has_diacritics=true")
        trace.append("L3S| ENTERING_MUARRAB_BRANCH: checking_diacritic_patterns")
        diacritic_positions = locate_araab(word_no_aspirate)
        trace.append(f"L3S| LOCATED_DIACRITICS: positions={len(diacritic_positions)},mask='{diacritic_positions}'")
        
        # ========================================================================
        # MUARRAB BRANCH: Diacritic-driven pattern matching
        # ========================================================================
        # NOTE ON PRIORITY:
        # Diacritic-driven rules always outrank character-driven rules
        # because they encode explicit phonetic intent, not inference.
        # Priority order (checked in sequence, first match wins):
        # 1. Jazm at position 1 (highest priority - most specific diacritic)
        # 2. Zer/Zabar/Paish at position 1 (vowel diacritics)
        # 3. Shadd at position 1 (gemination marker)
        # 4. Alif at position 2 (character pattern, lower priority than diacritics)
        # 5. Vowel at position 2 (character pattern)
        # 6. Vowel at center (position 1 or position 2 with 'ہ')
        # 7. Default muarrab pattern (fallback)
        # ========================================================================
        
        # Pattern 1: Jazm (sukoon) at position 1
        # Linguistic rule: Jazm indicates a consonant cluster or closed syllable.
        #                  This is the most specific diacritic pattern.
        if len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazm
            trace.append(f"L3S| CHECKING_DIACRITIC_AT_POSITION: pos=1,diacritic=jazm,character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}'")
            trace.append("L3S| PATTERN_CHECK_1: jazm_at_pos_1=true")
            
            # Sub-pattern 1a: Jazm with Alif Madd at start
            # Justification: Alif Madd (آ) at start + Jazm creates long-short-short pattern.
            #                The initial long syllable (آ) followed by jazm creates this specific rhythm.
            if word_no_diacritics[0] == 'آ':
                trace.append(f"L3S| CHECKING_SUB_CONDITION: first_char='{word_no_diacritics[0]}',is_alif_madd=true")
                code = "=--"  # Long-short-short: Alif Madd (long) + Jazm (short) + final (short)
                trace.append(f"L3S| PATTERN_MATCHED: diacritic=jazm_at_pos_1,first_char_is_alif_madd=true,branch=if,code={code}")
            
            # Sub-pattern 1b: Jazm without Alif Madd at start
            # Justification: Jazm alone creates short-long pattern.
            #                The jazm forces a short first syllable, followed by long second syllable.
            else:
                trace.append(f"L3S| CHECKING_SUB_CONDITION: first_char='{word_no_diacritics[0] if len(word_no_diacritics) > 0 else 'N/A'}',is_alif_madd=false")
                code = "=-"  # Short-long: Jazm (short) + remaining (long)
                trace.append(f"L3S| PATTERN_MATCHED: diacritic=jazm_at_pos_1,first_char='{word_no_diacritics[0] if len(word_no_diacritics) > 0 else 'N/A'}',is_alif_madd=false,branch=else,ruled_out_patterns=[alif_madd],code={code}")
        
        # Pattern 2: Zer/Zabar/Paish at position 1
        # Linguistic rule: These diacritics (zer=kasra, zabar=fatha, paish=damma) indicate
        #                  vowel sounds, creating short-long pattern.
        # Justification: Vowel diacritics at position 1 create a short first syllable,
        #                followed by a long second syllable.
        elif len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                               diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                               diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
            diacritic_type = "zer" if diacritic_positions[1] == ARABIC_DIACRITICS[1] else ("zabar" if diacritic_positions[1] == ARABIC_DIACRITICS[8] else "paish")
            trace.append(f"L3S| CHECKING_DIACRITIC_AT_POSITION: pos=1,diacritic={diacritic_type},character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}'")
            trace.append(f"L3S| PATTERN_CHECK_2: {diacritic_type}_at_pos_1=true,ruled_out_patterns=[jazm]")
            code = "-="  # Short-long: Vowel diacritic (short) + remaining (long)
            trace.append(f"L3S| PATTERN_MATCHED: diacritic={diacritic_type}_at_pos_1,ruled_out_patterns=[jazm],code={code}")
        
        # Pattern 3: Shadd at position 1
        # Linguistic rule: Shadd indicates gemination (doubling) of the consonant.
        # Justification: Gemination creates a long first syllable, followed by long second syllable.
        #                  The doubled consonant extends the syllable length.
        elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[0]:  # shadd
            trace.append(f"L3S| CHECKING_DIACRITIC_AT_POSITION: pos=1,diacritic=shadd,character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}'")
            trace.append("L3S| PATTERN_CHECK_3: shadd_at_pos_1=true,ruled_out_patterns=[jazm,zer/zabar/paish]")
            code = "=="  # Long-long: Shadd (long via gemination) + remaining (long)
            trace.append(f"L3S| PATTERN_MATCHED: diacritic=shadd_at_pos_1,ruled_out_patterns=[jazm,zer/zabar/paish],code={code}")
        
        # Pattern 4: Alif at position 2
        # Linguistic rule: Alif (ا) at center position acts as a long vowel nucleus.
        # Justification: Alif in the middle creates short-long pattern.
        #                First syllable is short, second syllable (with alif) is long.
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=2,character='{word_no_diacritics[2]}'")
            trace.append("L3S| PATTERN_CHECK_4: alif_at_pos_2=true,ruled_out_patterns=[jazm,zer/zabar/paish,shadd]")
            code = "-="  # Short-long: First (short) + Alif at pos 2 (long)
            trace.append(f"L3S| PATTERN_MATCHED: alif_at_pos_2,ruled_out_patterns=[jazm,zer/zabar/paish,shadd],code={code}")
        
        # Pattern 5: Vowel at position 2 (end position)
        # Linguistic rule: Vowels (ا, ی, ے, و, ہ) at the end position create flexible patterns.
        # Justification: The pattern depends on what's at position 1.
        #                If position 1 is alif, we get short-long. Otherwise, short-long.
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] in ['ا', 'ی', 'ے', 'و', 'ہ']:  # vowels at end
            vowel_char = word_no_diacritics[2]
            trace.append(f"L3S| CHECKING_VOWEL_AT_POSITION: pos=2,character='{vowel_char}'")
            trace.append(f"L3S| PATTERN_CHECK_5: vowel_at_pos_2='{vowel_char}',ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2]")
            
            # Sub-pattern 5a: Vowel at end with Alif at position 1
            # Justification: Alif at position 1 + vowel at end creates short-long pattern.
            #                The alif at position 1 creates a short first syllable.
            if word_no_diacritics[1] == 'ا':
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_1_character='{word_no_diacritics[1]}',is_alif=true")
                code = "=-"  # Short-long: Alif at pos 1 (short) + vowel at end (long)
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_pos_2='{vowel_char}',alif_at_pos_1=true,branch=if,code={code}")
            
            # Sub-pattern 5b: Vowel at end without Alif at position 1
            # Justification: Vowel at end without alif at position 1 creates short-long pattern.
            #                First syllable is short, second syllable (ending in vowel) is long.
            else:
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_1_character='{word_no_diacritics[1] if len(word_no_diacritics) > 1 else 'N/A'}',is_alif=false")
                code = "-="  # Short-long: First (short) + vowel at end (long)
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_pos_2='{vowel_char}',alif_at_pos_1=false,branch=else,code={code}")
        
        # Pattern 6: Vowel at center position
        # Linguistic rule: Vowels at center (position 1: ا, ی, ے, و) OR 'ہ' at position 2.
        # Justification: Vowel at center creates short-long pattern.
        #                The center vowel creates a short first syllable, long second syllable.
        elif _has_vowel_at_center(word_no_diacritics):  # vowels at center
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
            code = "=-"  # Short-long: First (short) + vowel at center (long)
            trace.append(f"L3S| PATTERN_MATCHED: vowel_at_pos_{vowel_pos}='{vowel_char}',ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2,vowel_at_pos_2],code={code}")
        
        # Pattern 7: Default muarrab pattern
        # Justification: When no specific pattern matches, use default short-long pattern.
        #                This is the fallback for muarrab words that don't match any specific rule.
        else:  # default case
            trace.append("L3S| PATTERN_CHECK_7: all_previous_checks_failed")
            trace.append("L3S| NO_PATTERN_MATCHED: using_default_muarrab_rule")
            code = "=-"  # Short-long: Default pattern for muarrab words
            trace.append(f"L3S| PATTERN_MATCHED: default_muarrab,ruled_out_patterns=[jazm,zer/zabar/paish,shadd,alif_at_pos_2,vowel_at_pos_2,vowel_at_center],code={code}")
    
    else:
        trace.append("L3S| WORD_NOT_MUARRAB: has_diacritics=false")
        trace.append("L3S| ENTERING_NON_MUARRAB_BRANCH: checking_character_patterns")
        
        # ========================================================================
        # NON-MUARRAB BRANCH: Character-driven pattern matching
        # ========================================================================
        # NOTE ON PRIORITY:
        # Diacritic-driven rules always outrank character-driven rules
        # because they encode explicit phonetic intent, not inference.
        # Priority order (checked in sequence, first match wins):
        # 1. Starts with Alif Madd (آ) - special long character
        # 2. Alif at position 1 - internal vowel nucleus
        # 3. Alif at position 2 - internal vowel nucleus at end
        # 4. Vowel at center (position 1: ی, ے, و, ہ)
        # 5. Vowel at end (position 2: ی, ے, و, ہ)
        # 6. Vowel plus h at start (flexible terminal)
        # 7. Default non-muarrab pattern (fallback)
        # ========================================================================
        
        # Pattern 1: Starts with Alif Madd (آ)
        # Linguistic rule: Alif Madd (آ) is a special long character that creates long-long pattern.
        # Justification: Alif Madd at start creates two long syllables.
        #                The آ itself is long, and it typically creates a long second syllable.
        if word_no_diacritics[0] == 'آ':
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=0,character='{word_no_diacritics[0]}'")
            trace.append("L3S| PATTERN_CHECK_1: starts_with_alif_madd=true")
            code = "=="  # Long-long: Alif Madd (long) + remaining (long)
            trace.append(f"L3S| PATTERN_MATCHED: starts_with_alif_madd_at_pos_0,code={code}")
        
        # Pattern 2: Alif at position 1 (center)
        # Linguistic rule: Alif (ا) acting as internal vowel nucleus.
        # Justification: Alif at center creates short-long pattern.
        #                First syllable is short, second syllable (with alif) is long.
        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':  # Alif at centre
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=1,character='{word_no_diacritics[1]}'")
            trace.append("L3S| PATTERN_CHECK_2: alif_at_pos_1=true,ruled_out_patterns=[alif_madd_at_pos_0]")
            code = "=-"  # Short-long: First (short) + Alif at pos 1 (long)
            trace.append(f"L3S| PATTERN_MATCHED: alif_at_pos_1,ruled_out_patterns=[alif_madd_at_pos_0],code={code}")
        
        # Pattern 3: Alif at position 2 (end)
        # Linguistic rule: Alif (ا) at end position acts as long vowel nucleus.
        # Justification: Alif at end creates short-long pattern.
        #                First syllable is short, second syllable (ending in alif) is long.
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
            trace.append(f"L3S| CHECKING_CHARACTER_AT_POSITION: pos=2,character='{word_no_diacritics[2]}'")
            trace.append("L3S| PATTERN_CHECK_3: alif_at_pos_2=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1]")
            code = "-="  # Short-long: First (short) + Alif at pos 2 (long)
            trace.append(f"L3S| PATTERN_MATCHED: alif_at_pos_2,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1],code={code}")
        
        # Pattern 4: Vowel at center (position 1: ی, ے, و, ہ)
        # Linguistic rule: Vowels at center position create patterns that depend on what follows.
        # Justification: The pattern varies based on what's at position 2.
        elif len(word_no_diacritics) > 1 and word_no_diacritics[1] in ['ی', 'ے', 'و', 'ہ']:  # vowels + h at centre
            trace.append(f"L3S| PATTERN_CHECK_4: vowel_at_center=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2]")
            
            # Sub-pattern 4a: Vowel at center with 'ہ' at end
            # Justification: Vowel at center + 'ہ' at end creates short-long pattern.
            #                The 'ہ' at end doesn't change the basic short-long structure.
            if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ہ':
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_2_character='{word_no_diacritics[2]}',is_haa=true")
                code = "=-"  # Short-long: First (short) + vowel at center + 'ہ' (long)
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_center,haa_at_end=true,branch=if,code={code}")
            
            # Sub-pattern 4b: Vowel at center with vowel at end
            # Justification: Vowel at center + vowel at end creates short-long pattern.
            #                The double vowel structure maintains short-long rhythm.
            elif len(word_no_diacritics) > 2 and word_no_diacritics[2] in ['ی', 'ے', 'و']:  # vowels + h at end
                trace.append(f"L3S| CHECKING_SUB_CONDITION: pos_2_character='{word_no_diacritics[2]}',is_vowel=true")
                code = "-="  # Short-long: First (short) + vowel at center + vowel at end (long)
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_center,vowel_at_end=true,branch=elif,code={code}")
            
            # Sub-pattern 4c: Vowel at center without special end
            # Justification: Vowel at center without special end character creates short-long pattern.
            #                Default behavior for center vowel.
            else:
                trace.append("L3S| CHECKING_SUB_CONDITION: pos_2_check=false,using_else_branch")
                code = "=-"  # Short-long: First (short) + vowel at center (long)
                trace.append(f"L3S| PATTERN_MATCHED: vowel_at_center,no_special_end,branch=else,code={code}")
        
        # Pattern 5: Vowel at end (position 2: ی, ے, و, ہ)
        # Linguistic rule: Vowels at end position create short-long pattern.
        # Justification: Vowel at end creates a long final syllable, with short first syllable.
        elif len(word_no_diacritics) > 2 and word_no_diacritics[2] in ['ی', 'ے', 'و', 'ہ']:  # vowels + h at end
            trace.append("L3S| PATTERN_CHECK_5: vowel_at_end=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center]")
            code = "-="  # Short-long: First (short) + vowel at end (long)
            trace.append(f"L3S| PATTERN_MATCHED: vowel_at_end,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center],code={code}")
        
        # Pattern 6: Vowel plus h at start
        # Linguistic rule: Vowel plus h (ہ) at start creates flexible terminal pattern.
        # Justification: This creates short-long pattern, similar to other vowel patterns.
        #                The vowel+h combination at start creates a short first syllable.
        elif len(word_no_diacritics) > 0 and is_vowel_plus_h(word_no_diacritics[0]):
            trace.append(f"L3S| PATTERN_CHECK_6: vowel_plus_h_at_start=true,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center,vowel_at_end]")
            code = "-="  # Short-long: Vowel+h at start (short) + remaining (long)
            trace.append(f"L3S| PATTERN_MATCHED: vowel_plus_h_at_start,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center,vowel_at_end],code={code}")
        
        # Pattern 7: Default non-muarrab pattern
        # Justification: When no specific pattern matches, use default short-long pattern.
        #                This is the fallback for non-muarrab words that don't match any specific rule.
        else:
            trace.append("L3S| PATTERN_CHECK_7: all_previous_checks_failed")
            code = "-="  # Short-long: Default pattern for non-muarrab words
            trace.append(f"L3S| PATTERN_MATCHED: default_non_muarrab,ruled_out_patterns=[alif_madd_at_pos_0,alif_at_pos_1,alif_at_pos_2,vowel_at_center,vowel_at_end,vowel_plus_h_at_start],code={code}")
    
    # ============================================================================
    # SECTION 3: POST-PROCESSING - Noon Ghunna adjustments
    # ============================================================================
    # Noon (ن) with jazm requires special handling due to nasalization (ghunna).
    # This adjustment modifies the code based on specific noon+jazm patterns.
    # Justification: Noon ghunna is a phonological phenomenon that affects scansion.
    #                It must be applied AFTER the main pattern matching to override
    #                certain patterns when noon+jazm is present.
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
    
    # ============================================================================
    # SECTION 1: NORMALIZATION/DELEGATION - Length-based delegation
    # ============================================================================
    # These patterns handle cases where the word collapses to fewer characters
    # after removing diacritics and aspirates. These are checked FIRST because
    # they represent degenerate cases that need special handling via delegation
    # to appropriate length-specific scan functions.
    
    # Pattern: Word collapses to single character after stripping
    # Justification: When a 4-character word collapses to one character after
    #                removing diacritics, delegate to length_one_scan.
    #                This is a defensive fallback; treat as standalone syllable.
    if len(word_no_diacritics) == 1:
        trace.append("L4S| STRIPPED_LENGTH_DELEGATE: length=1,delegate_to=L1S")
        # SINGLE_SYLLABLE: degenerate case after araab removal
        # Reason: defensive fallback; treat as standalone syllable
        code = length_one_scan(word_no_aspirate, trace=trace)
    
    # Pattern: Word collapses to two characters after stripping
    # Justification: When a 4-character word collapses to two characters after
    #                removing diacritics, delegate to length_two_scan.
    #                This preserves specialized two-character pattern matching.
    elif len(word_no_diacritics) == 2:
        trace.append("L4S| STRIPPED_LENGTH_DELEGATE: length=2,delegate_to=L2S")
        code = length_two_scan(word_no_aspirate, trace=trace)
    
    # Pattern: Word collapses to three characters after stripping
    # Justification: When a 4-character word collapses to three characters after
    #                removing diacritics, delegate to length_three_scan.
    #                This preserves specialized three-character pattern matching.
    elif len(word_no_diacritics) == 3:
        trace.append("L4S| STRIPPED_LENGTH_DELEGATE: length=3,delegate_to=L3S")
        code = length_three_scan(word_no_aspirate, trace=trace)
    
    else:
        # ============================================================================
        # SECTION 2: PREFIX SPLITS - Alif Madd prefix handling
        # ============================================================================
        # Pattern: Alif Madd (آ) at start
        # Linguistic rule: Alif Madd (آ) at start creates a long prefix syllable.
        # Justification: When Alif Madd is at position 0, split the word at position 1,
        #                prefix the result with "=" (long), and delegate the remainder
        #                to length_three_scan. This handles the long prefix pattern.
        if word_no_diacritics[0] == 'آ':
            # Remove first character and scan the rest
            remaining = word_no_aspirate[1:] if len(word_no_aspirate) > 1 else ""
            trace.append(f"L4S| SPLIT_AT_POSITION: split_pos=1,delegate_to=L3S,remaining={remaining}")
            code = "=" + length_three_scan(remaining, trace=trace)  # Long prefix + remainder
        
        # ============================================================================
        # SECTION 3: MUARRAB PATHS - Diacritic-driven pattern matching
        # ============================================================================
        # Priority order (checked in sequence, first match wins):
        # 1. Alif at position 1 (with/without jazm at position 2)
        # 2. Alif at position 2
        # 3. و (waw) at position 1 (with various diacritic combinations)
        # 4. ی (yeh) at position 1 (with various diacritic combinations)
        # 5. Complex diacritic pattern matching (zer/zabar/paish combinations)
        # 6. Default muarrab patterns
        # ============================================================================
        # NOTE: Diacritic-driven rules have higher priority than character-driven rules
        # because they encode explicit phonetic intent, not inference.
        elif is_muarrab(word_no_aspirate):
            trace.append("L4S| WORD_IS_MUARRAB: has_diacritics=true")
            diacritic_positions = locate_araab(word_no_aspirate)
            
            # Pattern 1: Alif at position 1
            # Linguistic rule: Alif (ا) at position 1 acts as internal vowel nucleus.
            # Justification: Alif at position 1 creates patterns based on diacritics at position 2.
            #                If jazm (sukoon) is at position 2, creates long-short-short pattern.
            #                Otherwise, creates long-long pattern.
            if len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ا':
                # Sub-pattern 1a: Alif at pos 1 with jazm at pos 2
                # Justification: Jazm at position 2 creates long-short-short pattern.
                #                The alif at position 1 is long, jazm creates short, final is short.
                if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                    code = "=--"  # Long-short-short: Alif at pos 1 (long) + jazm at pos 2 (short) + final (short)
                # Sub-pattern 1b: Alif at pos 1 without jazm at pos 2
                # Justification: Alif at position 1 without jazm creates long-long pattern.
                #                Both syllables are long.
                else:
                    code = "=="  # Long-long: Alif at pos 1 (long) + remaining (long)
            
            # Pattern 2: Alif at position 2
            # Linguistic rule: Alif (ا) at position 2 acts as long vowel nucleus.
            # Justification: Alif at position 2 creates short-long-short pattern.
            #                First syllable is short, alif at position 2 creates long, final is short.
            elif len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                code = "-=-"  # Short-long-short: First (short) + Alif at pos 2 (long) + final (short)
            
            else:
                # Pattern 3: و (waw) at position 1
                # Linguistic rule: و (waw) at position 1 creates patterns based on diacritics and endings.
                # Justification: The pattern depends on whether there's a 'ت' with jazm at position 3,
                #                or various diacritic combinations at positions 1 and 2.
                if len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'و':
                    # Sub-pattern 3a: و at pos 1 with 'ت' and jazm at pos 3
                    # Justification: 'ت' with jazm at position 3 creates short-long pattern.
                    #                The 'ت' with jazm forces a short final syllable.
                    if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ت' and len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazm
                        code = "=-"  # Short-long: First (short) + و at pos 1 (long) + 'ت' with jazm (short)
                    else:
                        # Sub-pattern 3b: و at pos 1 with zer/zabar/paish at pos 1
                        # Justification: Vowel diacritics at position 1 create short-long-short pattern.
                        #                The diacritics indicate vowel sounds that affect syllable structure.
                        if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            code = "-=-"  # Short-long-short: First (short) + و with diacritic (long) + final (short)
                        else:
                            # Sub-pattern 3c: و at pos 1 with jazm at pos 2
                            # Justification: Jazm at position 2 creates long-short-short pattern.
                            #                The jazm forces a short second syllable.
                            if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "=--"  # Long-short-short: First (long) + و with jazm (short) + final (short)
                            # Sub-pattern 3d: و at pos 1 default
                            # Justification: Default pattern for و at position 1 is long-long.
                            else:
                                code = "=="  # Long-long: First (long) + و at pos 1 (long) + final (long)
                
                # Pattern 4: ی (yeh) at position 1
                # Linguistic rule: ی (yeh) at position 1 creates patterns based on diacritics and endings.
                # Justification: The pattern depends on whether there's a 'ت' with jazm at position 3,
                #                or various diacritic combinations at positions 0, 1, and 2.
                elif len(word_no_diacritics) > 1 and word_no_diacritics[1] == 'ی':
                    # Sub-pattern 4a: ی at pos 1 with 'ت' and jazm at pos 3
                    # Justification: 'ت' with jazm at position 3 creates short-long pattern.
                    #                The 'ت' with jazm forces a short final syllable.
                    if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ت' and len(diacritic_positions) > 3 and diacritic_positions[3] == ARABIC_DIACRITICS[2]:  # jazm
                        code = "=-"  # Short-long: First (short) + ی at pos 1 (long) + 'ت' with jazm (short)
                    # Sub-pattern 4b: ی at pos 1 with zer/zabar/paish at pos 0
                    # Justification: Vowel diacritics at position 0 affect the pattern.
                    #                If also present at position 1, creates short-long-short pattern.
                    elif len(diacritic_positions) > 0 and (diacritic_positions[0] == ARABIC_DIACRITICS[1] or  # zer
                                           diacritic_positions[0] == ARABIC_DIACRITICS[8] or  # zabar
                                           diacritic_positions[0] == ARABIC_DIACRITICS[9]):  # paish
                        # Sub-pattern 4b-i: ی with zer/zabar/paish at both pos 0 and pos 1
                        # Justification: Vowel diacritics at both positions create short-long-short pattern.
                        if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            code = "-=-"  # Short-long-short: Diacritic at pos 0 (short) + ی with diacritic (long) + final (short)
                        else:
                            # Sub-pattern 4b-ii: ی with zer/zabar/paish at pos 0 and jazm at pos 2
                            # Justification: Jazm at position 2 creates long-short-short pattern.
                            if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "=--"  # Long-short-short: First (long) + ی with diacritic (short) + final (short)
                            # Sub-pattern 4b-iii: ی with zer/zabar/paish at pos 0 default
                            # Justification: Default pattern is long-long.
                            else:
                                code = "=="  # Long-long: First (long) + ی with diacritic (long) + final (long)
                    # Sub-pattern 4c: ی at pos 1 default
                    # Justification: Default pattern for ی at position 1 is long-long.
                    else:
                        code = "=="  # Long-long: First (long) + ی at pos 1 (long) + final (long)
                
                # Pattern 5: Complex diacritic pattern matching
                # Linguistic rule: Complex combinations of diacritics create various patterns.
                # Justification: The pattern depends on combinations of zer/zabar/paish and jazm
                #                at different positions, as well as character patterns.
                else:
                    # Sub-pattern 5a: zer/zabar/paish at position 0
                    # Justification: Vowel diacritics at position 0 affect syllable structure.
                    if len(diacritic_positions) > 0 and (diacritic_positions[0] == ARABIC_DIACRITICS[1] or  # zer
                                        diacritic_positions[0] == ARABIC_DIACRITICS[8] or  # zabar
                                        diacritic_positions[0] == ARABIC_DIACRITICS[9]):  # paish
                        # Sub-pattern 5a-i: zer/zabar/paish at both pos 0 and pos 1
                        # Justification: Vowel diacritics at both positions create complex patterns
                        #                based on what follows (vowel at pos 2, jazm at pos 2, or default).
                        if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                            diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                            diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                            # Sub-pattern 5a-i-1: Vowel plus h at position 2
                            # Justification: Vowel plus h at position 2 creates short-long-short pattern.
                            if len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                                code = "-=-"  # Short-long-short: Diacritic at pos 0 (short) + diacritic at pos 1 (long) + vowel+h (short)
                            # Sub-pattern 5a-i-2: Jazm at position 2
                            # Justification: Jazm at position 2 creates short-long-short pattern.
                            elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                                code = "-=-"  # Short-long-short: Diacritic at pos 0 (short) + diacritic at pos 1 (long) + jazm (short)
                            # Sub-pattern 5a-i-3: Default with double diacritics
                            # Justification: Default pattern with double diacritics is short-short-long.
                            else:
                                code = "--="  # Short-short-long: Diacritic at pos 0 (short) + diacritic at pos 1 (short) + final (long)
                        # Sub-pattern 5a-ii: zer/zabar/paish at pos 0 with jazm at pos 1
                        # Justification: Jazm at position 1 creates long-long pattern.
                        elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "=="  # Long-long: Diacritic at pos 0 (long) + jazm at pos 1 (long) + final (long)
                        # Sub-pattern 5a-iii: zer/zabar/paish at pos 0 with jazm at pos 2
                        # Justification: Jazm at position 2 creates short-long-short pattern.
                        elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "-=-"  # Short-long-short: Diacritic at pos 0 (short) + remaining (long) + jazm (short)
                        # Sub-pattern 5a-iv: zer/zabar/paish at pos 0 with alif/yeh at pos 3
                        # Justification: Alif or yeh at position 3 creates short-short-long pattern.
                        else:
                            if len(word_no_diacritics) > 3 and (word_no_diacritics[3] == 'ا' or word_no_diacritics[3] == 'ی'):
                                code = "--="  # Short-short-long: Diacritic at pos 0 (short) + remaining (short) + alif/yeh (long)
                            # Sub-pattern 5a-v: zer/zabar/paish at pos 0 default
                            # Justification: Default pattern is short-long-short.
                            else:
                                code = "-=-"  # Short-long-short: Diacritic at pos 0 (short) + remaining (long) + final (short)
                    # Sub-pattern 5b: Jazm at position 1
                    # Justification: Jazm at position 1 creates patterns based on what's at position 2.
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        # Sub-pattern 5b-i: Jazm at both pos 1 and pos 2
                        # Justification: Double jazm creates long-long pattern.
                        if len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                            code = "=="  # Long-long: First (long) + jazm at pos 1 (long) + jazm at pos 2 (long)
                        # Sub-pattern 5b-ii: Jazm at pos 1 only
                        # Justification: Jazm at position 1 creates long-short-short pattern.
                        else:
                            code = "=--"  # Long-short-short: First (long) + jazm at pos 1 (short) + final (short)
                    # Sub-pattern 5c: Jazm at position 2
                    # Justification: Jazm at position 2 creates short-long-short pattern.
                    elif len(diacritic_positions) > 2 and diacritic_positions[2] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "-=-"  # Short-long-short: First (short) + remaining (long) + jazm at pos 2 (short)
                    # Sub-pattern 5d: zer/zabar/paish at position 2
                    # Justification: Vowel diacritics at position 2 create long-long pattern.
                    elif len(diacritic_positions) > 2 and (diacritic_positions[2] == ARABIC_DIACRITICS[1] or  # zer
                                          diacritic_positions[2] == ARABIC_DIACRITICS[8] or  # zabar
                                          diacritic_positions[2] == ARABIC_DIACRITICS[9]):  # paish
                        code = "=="  # Long-long: First (long) + remaining (long) + diacritic at pos 2 (long)
                    # Sub-pattern 5e: Vowel plus h at position 2
                    # Justification: Vowel plus h at position 2 creates short-long-short pattern.
                    elif len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                        code = "-=-"  # Short-long-short: First (short) + remaining (long) + vowel+h (short)
                    # Sub-pattern 5f: Default muarrab pattern
                    # Justification: When no specific pattern matches, use default long-long pattern.
                    #                This is the fallback for muarrab words that don't match any specific rule.
                    else:
                        code = "=="  # Long-long: Default pattern for muarrab words
        
        # ============================================================================
        # SECTION 4: NON-MUARRAB VOWEL PATHS - Character-driven vowel pattern matching
        # ============================================================================
        # Pattern: Vowel plus h at position 2
        # Linguistic rule: Vowel plus h (ا،ی،ے،و،ہ) at position 2 creates patterns
        #                  based on what follows or precedes.
        # Justification: The pattern depends on whether there's an alif at position 3,
        #                or a vowel plus h at position 1, or defaults to short-long-short.
        elif len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
            # Sub-pattern 4a: Vowel plus h at pos 2 with alif at pos 3
            # Justification: Alif at position 3 creates long-long pattern.
            #                The alif extends the final syllable to long.
            if len(word_no_diacritics) > 3 and word_no_diacritics[3] == 'ا':
                code = "=="  # Long-long: First (long) + vowel+h at pos 2 (long) + alif at pos 3 (long)
            # Sub-pattern 4b: Vowel plus h at both pos 1 and pos 2
            # Justification: Vowel plus h at both positions creates long-long pattern.
            #                The double vowel structure maintains long syllables.
            elif len(word_no_diacritics) > 1 and is_vowel_plus_h(word_no_diacritics[1]):
                code = "=="  # Long-long: First (long) + vowel+h at pos 1 (long) + vowel+h at pos 2 (long)
            # Sub-pattern 4c: Vowel plus h at pos 2 default
            # Justification: Default pattern for vowel plus h at position 2 is short-long-short.
            #                First syllable is short, vowel+h creates long, final is short.
            else:
                code = "-=-"  # Short-long-short: First (short) + vowel+h at pos 2 (long) + final (short)
        
        # ============================================================================
        # SECTION 5: DEFAULT CONSONANTAL PATHS - Default non-muarrab pattern
        # ============================================================================
        # Pattern: Default consonantal pattern
        # Linguistic rule: Words without diacritics and without specific vowel patterns
        #                  default to long-long pattern.
        # Justification: When no specific pattern matches, use default long-long pattern.
        #                This is the fallback for non-muarrab words that don't match
        #                any specific rule (no diacritics, no special vowel patterns).
        else:  # default
            code = "=="  # Long-long: Default pattern for non-muarrab consonantal words
            trace.append("L4S| PATTERN_MATCHED: default_non_muarrab,code====")
        trace.append(f"L4S| PATTERN_MATCHED: pattern=non_muarrab_vowel_check,code={code}")
    
    # ============================================================================
    # SECTION 6: POST-DECISION REPAIRS - Noon Ghunna adjustments
    # ============================================================================
    # Noon (ن) with jazm requires special handling due to nasalization (ghunna).
    # This adjustment modifies the code based on specific noon+jazm patterns.
    # Justification: Noon ghunna is a phonological phenomenon that affects scansion.
    #                It must be applied AFTER the main pattern matching to override
    #                certain patterns when noon+jazm is present.
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
    
    # ============================================================================
    # SECTION 1: NORMALIZATION AND EARLY SPECIAL-CASE EXITS
    # ============================================================================
    # These patterns handle special cases that require early exit before
    # any other processing. These are checked FIRST because they represent
    # specific phonological phenomena that override normal pattern matching.
    
    # Pattern: Aspirated + ی (yeh) special case
    # Linguistic rule: Aspirated consonant (ھ) followed by ی (yeh) forces
    #                  a short medial vowel pattern.
    # Justification: This is a special phonological pattern (e.g., اندھیرے)
    #                that requires short medial vowel. This pattern must be
    #                checked before any other processing and returns early.
    # --- FIX: aspirated + ی should force short medial vowel (e.g. اندھیرے) ---
    if 'ھ' in word:
        for i in range(len(word) - 2):
            if word[i+1] == 'ھ' and word[i+2] == 'ی':
                trace.append(f"L5S| DETECTED_ASPIRATED_YEH_PATTERN: start_pos={i+1},end_pos={i+2}")
                trace.append("L5S| EARLY_RETURN_ASPIRATED_YEH_PATTERN: return_code=-==")
                logger.debug(f"length_five_scan: Early return for aspirated+ی pattern, returning '-=='")
                return "-=="  # Short-long-long: Aspirated+ی forces short medial vowel
    
    # ============================================================================
    # SECTION 2: DELEGATION TO SHORTER SCANNERS
    # ============================================================================
    # These patterns handle cases where the word collapses to fewer characters
    # after removing diacritics and aspirates. These are checked SECOND because
    # they represent degenerate cases that need special handling via delegation
    # to appropriate length-specific scan functions.
    
    # Pattern: Word collapses to three characters after stripping
    # Justification: When a 5+ character word collapses to three characters after
    #                removing diacritics, delegate to length_three_scan.
    #                This preserves specialized three-character pattern matching.
    if len(word_no_diacritics) == 3:
        trace.append("L5S| STRIPPED_LENGTH_DELEGATE: length=3,delegate_to=L3S")
        logger.debug(f"length_five_scan: Stripped length is 3, delegating to length_three_scan")
        code = length_three_scan(word, trace=trace)
    
    # Pattern: Word collapses to four characters after stripping
    # Justification: When a 5+ character word collapses to four characters after
    #                removing diacritics, delegate to length_four_scan.
    #                This preserves specialized four-character pattern matching.
    elif len(word_no_diacritics) == 4:
        trace.append("L5S| STRIPPED_LENGTH_DELEGATE: length=4,delegate_to=L4S")
        logger.debug(f"length_five_scan: Stripped length is 4, delegating to length_four_scan")
        code = length_four_scan(word, trace=trace)
    
    else:
        # ============================================================================
        # SECTION 3: PREFIX-DRIVEN SPLIT DECISIONS - Alif Madd prefix handling
        # ============================================================================
        # Pattern: Alif Madd (آ) at start
        # Linguistic rule: Alif Madd (آ) at start creates a long prefix syllable.
        # Justification: When Alif Madd is at position 0, split the word at position 2
        #                (آ + next character), prefix the result with "=" (long), and
        #                delegate the remainder to length_four_scan. This handles the
        #                long prefix pattern for 5+ character words.
        if word_no_diacritics[0] == 'آ':
            # Remove first 2 characters (آ + next) and scan the rest
            remaining = word_no_aspirate[2:] if len(word_no_aspirate) > 2 else ""
            trace.append(f"L5S| SPLIT_AT_POSITION: split_pos=2,delegate_to=L4S,remaining={remaining}")
            logger.debug(f"length_five_scan: Split at position 2 (آ pattern): prefix='{word_no_aspirate[:2]}', remaining='{remaining}'")
            code = "=" + length_four_scan(remaining, trace=trace)  # Long prefix + remainder
        
        # ============================================================================
        # SECTION 4: MUARRAB (DIACRITIC-DRIVEN) DECISION PATHS
        # ============================================================================
        # Priority order (checked in sequence, first match wins):
        # 1. Alif at positions 2, 3, or 4 (with various diacritic combinations)
        # 2. و/ی (waw/yeh) at positions 1, 2, or 3 (with various diacritic combinations)
        # 3. Complex diacritic pattern matching (zer/zabar/paish/jazm combinations)
        # 4. Default muarrab patterns
        # ============================================================================
        # NOTE: Diacritic-driven rules have higher priority than character-driven rules
        # because they encode explicit phonetic intent, not inference.
        elif is_muarrab(word_no_aspirate):
            trace.append("L5S| WORD_IS_MUARRAB: has_diacritics=true")
            logger.debug(f"length_five_scan: Word is muarrab (has diacritics), using muarrab path")
            diacritic_positions = locate_araab(word_no_aspirate)
            
            # Pattern 1: Alif at positions 2, 3, or 4
            # Linguistic rule: Alif (ا) at positions 2, 3, or 4 acts as long vowel nucleus.
            # Justification: The pattern depends on the specific position and surrounding
            #                diacritics. Position 3 alif may have special endings, position 2
            #                alif may trigger splits, position 4 alif has character-specific rules.
            if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'ا' or word_no_diacritics[2] == 'ا' or word_no_diacritics[3] == 'ا'):  # check alif at position 2,3,4
                trace.append("L5S| MUARRAB_PATH_ALIF_DETECTED: checking_positions_2_3_4")
                
                # Sub-pattern 1a: Alif at position 3
                # Justification: Alif at position 3 creates short-long-long pattern, unless
                #                followed by hamza/ye ending which creates flexible terminal.
                # Position 3 Alif
                if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                    trace.append("L5S| ALIF_POSITION_DETECTED: position=3")
                    # If alif is followed by hamza/ye ending, final syllable is ambiguous
                    # Justification: Hamza (ئ) or ye (ے) ending creates flexible terminal pattern.
                    #                The final syllable can be either long or short.
                    if 'ئ' in word_no_diacritics[3:] or word_no_diacritics.endswith('ے'):
                        code = "-=x"  # Short-long-flexible: First (short) + Alif at pos 3 (long) + flexible ending
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_3_with_hamza_ye_ending,code={code}")
                        logger.debug(f"length_five_scan: Position 3 Alif with hamza/ye ending: code='{code}'")
                    else:
                        code = "-=="  # Short-long-long: First (short) + Alif at pos 3 (long) + final (long)
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_3_default,code={code}")
                        logger.debug(f"length_five_scan: Position 3 Alif: code='{code}'")
                
                # Sub-pattern 1b: Alif at position 2
                # Justification: Alif at position 2 may trigger word splits based on
                #                diacritic patterns at positions 0 and 1. The split position
                #                depends on which positions have muarrab diacritics.
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
                            code = "=" + length_three_scan(remaining, trace=trace)  # Long prefix + remainder
                
                # Sub-pattern 1c: Alif at position 4
                # Justification: Alif at position 4 creates long-long-short pattern by default,
                #                but may be modified by diacritics at position 1 or character
                #                patterns at position 0 (especially 'ب' with various following characters).
                # Position 4 Alif
                else:
                    trace.append("L5S| ALIF_POSITION_DETECTED: position=4")
                    code = "==-"  # Long-long-short: First two (long) + Alif at pos 4 (long) + final (short)
                    # Justification: Diacritics at position 1 modify the pattern
                    if len(diacritic_positions) > 1 and (diacritic_positions[1] == ARABIC_DIACRITICS[1] or  # zer
                                         diacritic_positions[1] == ARABIC_DIACRITICS[8] or  # zabar
                                         diacritic_positions[1] == ARABIC_DIACRITICS[9]):  # paish
                        code = "--=-"  # Short-short-long-short: Diacritic at pos 1 (short) + remaining (short) + Alif (long) + final (short)
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_diacritic_zer_zabar_paish_at_1,code={code}")
                        logger.debug(f"length_five_scan: Position 4 Alif with zer/zabar/paish at diacritic_positions[1]: code='{code}'")
                    elif len(diacritic_positions) > 1 and diacritic_positions[1] == ARABIC_DIACRITICS[2]:  # jazr
                        code = "--=-"  # Short-short-long-short: Jazm at pos 1 (short) + remaining (short) + Alif (long) + final (short)
                        trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_4_diacritic_jazr_at_1,code={code}")
                        logger.debug(f"length_five_scan: Position 4 Alif with jazr at diacritic_positions[1]: code='{code}'")
                    # Justification: Character 'ب' at position 0 with specific following characters
                    #                modifies the pattern, otherwise defaults to --=-
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
                # Pattern 2: و/ی (waw/yeh) at positions 1, 2, or 3
                # Linguistic rule: و (waw) or ی (yeh) at positions 1, 2, or 3 create patterns
                #                  based on surrounding diacritics. These patterns may trigger
                #                  word splits or create specific code patterns.
                # Justification: The pattern depends on the specific position, surrounding
                #                diacritics (jazm, zer/zabar/paish), and whether muarrab
                #                diacritics are present at various positions.
                if len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'و' or word_no_diacritics[2] == 'و' or word_no_diacritics[3] == 'و' or
                                         word_no_diacritics[1] == 'ی' or word_no_diacritics[2] == 'ی' or word_no_diacritics[3] == 'ی'):
                    trace.append("L5S| MUARRAB_PATH_VOWEL_DETECTED: و/ی_at_positions_1_2_3")
                    # Sub-pattern 2a: و/ی at position 1
                    # Justification: و/ی at position 1 creates complex patterns based on
                    #                diacritics at positions 1, 2, and 3. May trigger splits
                    #                or create specific code patterns.
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
        
        # ============================================================================
        # SECTION 5: NON-MUARRAB ALIF-DRIVEN PATTERNS - Character-driven alif patterns
        # ============================================================================
        # Pattern: Alif at positions 2, 3, or 4 (non-muarrab)
        # Linguistic rule: Alif (ا) at positions 2, 3, or 4 acts as long vowel nucleus
        #                  in non-muarrab words (without diacritics).
        # Justification: The pattern depends on the specific position and surrounding
        #                character patterns. Position 3 alif is straightforward,
        #                position 2 alif may have complex patterns with vowels,
        #                position 4 alif has character-specific rules (especially 'ب').
        elif len(word_no_diacritics) > 1 and (word_no_diacritics[1] == 'ا' or word_no_diacritics[2] == 'ا' or word_no_diacritics[3] == 'ا'):  # check alif at position 2,3,4
            trace.append("L5S| NON_MUARRAB_PATH_ALIF_DETECTED: checking_positions_2_3_4")
            logger.debug(f"length_five_scan: Non-muarrab path with alif at position 2,3, or 4")
            
            # Sub-pattern 5a: Alif at position 3
            # Justification: Alif at position 3 creates short-long-long pattern.
            # Position 3 Alif
            if len(word_no_diacritics) > 2 and word_no_diacritics[2] == 'ا':
                trace.append("L5S| ALIF_POSITION_DETECTED: position=3_non_muarrab")
                code = "-=="  # Short-long-long: First (short) + Alif at pos 3 (long) + final (long)
                trace.append(f"L5S| PATTERN_MATCHED: alif_at_pos_3_non_muarrab,code={code}")
                logger.debug(f"length_five_scan: Position 3 Alif (non-muarrab): code='{code}' (no split)")
            
            # Sub-pattern 5b: Alif at position 2
            # Justification: Alif at position 2 creates patterns based on what follows.
            #                May have alif at position 3, vowels at positions 3/4, or default.
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
            
            # Sub-pattern 5c: Alif at position 4
            # Justification: Alif at position 4 creates long-long-short pattern by default,
            #                but may be modified by character patterns at position 0
            #                (especially 'ب' with various following characters).
            # Position 4 Alif
            else:
                trace.append("L5S| ALIF_POSITION_DETECTED: position=4_non_muarrab")
                code = "==-"  # Long-long-short: First two (long) + Alif at pos 4 (long) + final (short)
                logger.debug(f"length_five_scan: Position 4 Alif (non-muarrab): initial code='{code}'")
                # Justification: Character 'ب' at position 0 with specific following characters
                #                modifies the pattern, otherwise keeps default ==-
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
        
        # ============================================================================
        # SECTION 6: NON-MUARRAB VOWEL-DRIVEN PATTERNS - Character-driven vowel patterns
        # ============================================================================
        # Pattern: Vowel plus h at positions 1, 2, or 3 (non-muarrab)
        # Linguistic rule: Vowels plus h (ا،ی،ے،و،ہ) at positions 1, 2, or 3 create
        #                  patterns based on their position and surrounding characters.
        # Justification: The pattern depends on the specific position and what follows.
        #                Position 3 vowel is straightforward, position 2 vowel has
        #                complex patterns, position 4 vowel has character-specific rules.
        elif len(word_no_diacritics) > 1 and (is_vowel_plus_h(word_no_diacritics[1]) or is_vowel_plus_h(word_no_diacritics[2]) or is_vowel_plus_h(word_no_diacritics[3])):  # check vowels at position 2,3,4
            trace.append("L5S| NON_MUARRAB_PATH_VOWEL_DETECTED: checking_positions_2_3_4")
            logger.debug(f"length_five_scan: Non-muarrab path with vowels at position 2,3, or 4")
            
            # Sub-pattern 6a: Vowel at position 3
            # Justification: Vowel at position 3 creates short-long-long pattern,
            #                or short-long-long if also at position 4.
            # Position 3 Vowel
            if len(word_no_diacritics) > 2 and is_vowel_plus_h(word_no_diacritics[2]):
                trace.append(f"L5S| VOWEL_POSITION_DETECTED: position=3_non_muarrab,char={word_no_diacritics[2]}")
                code = "-=="  # Short-long-long: First (short) + Vowel at pos 3 (long) + final (long)
                if len(word_no_diacritics) > 3 and is_vowel_plus_h(word_no_diacritics[3]):
                    code = "-=="  # Short-long-long: First (short) + Vowel at pos 3 (long) + Vowel at pos 4 (long)
                    trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_3_and_4_non_muarrab,code={code}")
                else:
                    trace.append(f"L5S| PATTERN_MATCHED: vowel_at_pos_3_non_muarrab,code={code}")
                logger.debug(f"length_five_scan: Position 3 Vowel: code='{code}' (no split)")
            
            # Sub-pattern 6b: Vowel at position 2
            # Justification: Vowel at position 2 creates complex patterns based on
            #                what follows (vowels at positions 3/4, or default).
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
            
            # Sub-pattern 6c: Vowel at position 4
            # Justification: Vowel at position 4 creates long-long-short pattern by default,
            #                but may be modified by character patterns at position 0
            #                (especially 'ب' with various following characters).
            #                May also have special adjustment for 'ی' + 'ت' ending.
            # Position 4 Vowel
            else:
                trace.append("L5S| VOWEL_POSITION_DETECTED: position=4_non_muarrab")
                code = "==-"  # Long-long-short: First two (long) + Vowel at pos 4 (long) + final (short)
                # Justification: Character 'ب' at position 0 with specific following characters
                #                modifies the pattern, otherwise keeps default ==-
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
    
    # ============================================================================
    # SECTION 7: POST-DECISION REPAIRS AND ADJUSTMENTS
    # ============================================================================
    # These adjustments are applied AFTER the main pattern matching to handle
    # special phonological phenomena that override or modify the initial code.
    
    # Pattern 1: Noon Ghunna adjustments
    # Linguistic rule: Noon (ن) with jazm requires special handling due to nasalization (ghunna).
    # Justification: Noon ghunna is a phonological phenomenon that affects scansion.
    #                It must be applied AFTER the main pattern matching to override
    #                certain patterns when noon+jazm is present.
    # Apply noon ghunna adjustments if needed
    if contains_noon(word_no_diacritics):
        old_code = code
        code = noon_ghunna(word, code)
        if old_code != code:
            trace.append(f"L5S| APPLIED_NOON_GHUNNA_ADJUSTMENT: old_code={old_code},new_code={code}")
            logger.debug(f"length_five_scan: Applied noon ghunna adjustment: '{old_code}' -> '{code}'")

    # Pattern 2: Yaa (ے) adjustment
    # Linguistic rule: Words ending in 'ے' (yaa) with code ending in "==" should
    #                  have the final "=" changed to "x" (flexible terminal).
    # Justification: This creates a flexible terminal pattern, allowing the final
    #                syllable to be either long or short depending on metrical context.
    # Apply yaa adjustment if needed
    if code.endswith("==") and word_no_diacritics.endswith("ے"):
        new_code = code[:-1] + "x"  # Replace final "=" with "x" for flexible terminal
        trace.append(f"L5S| APPLIED_YAA_ADJUSTMENT: old_code={code},new_code={new_code}")
        logger.debug(f"length_five_scan: Applying yaa adjustment: '{code}' -> '{new_code}'")
        code = new_code

    trace.append(f"L5S| RETURNING: code={code}")
    logger.debug(f"length_five_scan: Final code for '{word}' = '{code}'")
    return code
