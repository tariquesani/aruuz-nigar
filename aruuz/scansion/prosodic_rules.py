"""
Prosodic Rules - Line-Level Transformations

Stateless class with static methods for applying prosodic rules
to lines (Al prefix, Izafat, Ataf, Word Grafting).
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aruuz.models import Lines

from .word_analysis import is_vowel_plus_h, is_consonant_plus_consonant, is_izafat
from aruuz.utils.araab import remove_araab, ARABIC_DIACRITICS
from .explain_logging import get_explain_logger


class ProsodicRules:
    """
    Stateless class for applying prosodic rules to lines.
    
    All methods are static methods (pure transformations).
    Call ordering must match current implementation:
    Al → Izafat → Ataf → Word Grafting
    """
    
    @staticmethod
    def process_al_prefix(line: 'Lines') -> None:
        """
        Process Al (ال) prefix logic.
        
        Modify codes when next word starts with "ال" and current word ends with zabar or paish.
        Extracted from match_line_to_meters() lines 1313-1366.
        
        Args:
            line: Lines instance to process (modified in-place)
        """
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
                            al_applied = False
                            # Process each code in current word
                            for k in range(len(wrd.code)):
                                if is_vowel_plus_h(stripped[length - 1]):
                                    # Last char is vowel+h: modify ending ("=" or "x" → "=", "-" → "=")
                                    if len(wrd.code[k]) > 0:
                                        last_char = wrd.code[k][-1]
                                        if last_char == "=" or last_char == "x":
                                            wrd.code[k] = wrd.code[k][:-1] + "="
                                            al_applied = True
                                        elif last_char == "-":
                                            wrd.code[k] = wrd.code[k][:-1] + "="
                                            al_applied = True
                                else:
                                    # Last char is consonant
                                    if length == 2 and is_consonant_plus_consonant(wrd.word):
                                        # 2-char words with consonant+consonant: modify to "=="
                                        if len(wrd.code[k]) > 0:
                                            wrd.code[k] = wrd.code[k][:-1] + "=="
                                            al_applied = True
                                    else:
                                        # Otherwise: modify ending ("=" or "x" → "-=", "-" → "=")
                                        if len(wrd.code[k]) > 0:
                                            last_char = wrd.code[k][-1]
                                            if last_char == "=" or last_char == "x":
                                                wrd.code[k] = wrd.code[k][:-1] + "-="
                                                al_applied = True
                                            elif last_char == "-":
                                                wrd.code[k] = wrd.code[k][:-1] + "="
                                                al_applied = True
                            
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
                            
                            # Log Al prefix rule application
                            if al_applied:
                                # Record per-word prosodic transformation steps
                                wrd.prosodic_transformation_steps.append("EXTENDED_PREVIOUS_WORD_TO_ABSORB_AL")
                                nwrd.prosodic_transformation_steps.append("MERGED_AL_WITH_PREVIOUS_WORD")

                                explain_logger = get_explain_logger()
                                explain_logger.info(f"RULE | Al prefix | Applied to Word {i+1} ('{nwrd.word}') | Modified Word {i}: codes updated, removed 'ال'")
    
    @staticmethod
    def process_izafat(line: 'Lines') -> None:
        """
        Process Izafat (اضافت) logic.
        
        Adjust codes for possessive markers.
        Extracted from match_line_to_meters() lines 1367-1407.
        
        Args:
            line: Lines instance to process (modified in-place)
        """
        # Adjust codes for possessive markers
        for wrd in line.words_list:
            if is_izafat(wrd.word):
                izafat_applied = False
                if len(wrd.id) > 0:
                    # Word has database ID
                    count = len(wrd.code)
                    for k in range(count):
                        t_word = remove_araab(wrd.word)
                        
                        # Arabic Monosyllabic Words (2-character words)
                        if wrd.length == 2:
                            wrd.code[k] = "xx"
                            izafat_applied = True
                        # Words ending in "ا" or "و"
                        elif len(wrd.code[k]) > 0 and (wrd.code[k][-1] == "=" or wrd.code[k][-1] == "x"):
                            if len(t_word) > 0 and (t_word[-1] == 'ا' or t_word[-1] == 'و'):
                                # Modify ending: "=" or "x" → "=x"
                                wrd.code[k] = wrd.code[k][:-1] + "=x"
                                izafat_applied = True
                            else:
                                # Words ending in "ی"
                                if len(t_word) > 0 and t_word[-1] == 'ی':
                                    # Add alternative code (original + "x")
                                    wrd.code.append(wrd.code[k] + "x")
                                    # Modify current code: "=" or "x" → "-x"
                                    wrd.code[k] = wrd.code[k][:-1] + "-x"
                                    izafat_applied = True
                                else:
                                    # Other cases: "=" or "x" → "-x"
                                    wrd.code[k] = wrd.code[k][:-1] + "-x"
                                    izafat_applied = True
                        # Words ending with "-"
                        elif len(wrd.code[k]) > 0 and wrd.code[k][-1] == "-":
                            # Modify ending: "-" → "x"
                            wrd.code[k] = wrd.code[k][:-1] + "x"
                            izafat_applied = True
                else:
                    # Word has no database ID
                    for k in range(len(wrd.code)):
                        if len(wrd.code[k]) > 0 and (wrd.code[k][-1] == "=" or wrd.code[k][-1] == "x"):
                            # Modify ending: "=" or "x" → "-x"
                            wrd.code[k] = wrd.code[k][:-1] + "-x"
                            izafat_applied = True
                        elif len(wrd.code[k]) > 0 and wrd.code[k][-1] == "-":
                            # Modify ending: "-" → "x"
                            wrd.code[k] = wrd.code[k][:-1] + "x"
                            izafat_applied = True
                
                # Log Izafat rule application (after all modifications)
                if izafat_applied:
                    wrd.prosodic_transformation_steps.append("APPLIED_IZAFAT_ADJUSTMENT_TO_FINAL_SYLLABLE")
                    explain_logger = get_explain_logger()
                    codes_str = ', '.join(wrd.code) if wrd.code else 'none'
                    explain_logger.info(f"RULE | Izafat | Applied to Word '{wrd.word}' | Modified codes: {codes_str}")
    
    @staticmethod
    def process_ataf(line: 'Lines') -> None:
        """
        Process Ataf (عطف) logic.
        
        Handle conjunction "و" between words.
        Extracted from match_line_to_meters() lines 1409-1475.
        
        Args:
            line: Lines instance to process (modified in-place)
        """
        # Handle conjunction "و" between words
        for i in range(1, len(line.words_list)):
            wrd = line.words_list[i]
            pwrd = line.words_list[i - 1]
            
            if wrd.word == "و":
                stripped = remove_araab(pwrd.word)
                length = len(stripped)
                
                if length > 0:
                    # Capture original codes for logging
                    original_codes = pwrd.code.copy() if pwrd.code else []
                    previous_modified = False
                    conjunction_cleared = False
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
                                        previous_modified = True
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            if wrd.code[j] != "":
                                                wrd.code[j] = ""
                                                conjunction_cleared = True
                                    elif last_char == "-":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                        previous_modified = True
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            if wrd.code[j] != "":
                                                wrd.code[j] = ""
                                                conjunction_cleared = True
                            else:
                                # Other vowels: modify code and clear current word codes
                                if len(pwrd.code[k]) > 0:
                                    last_char = pwrd.code[k][-1]
                                    if last_char == "=" or last_char == "x":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                        previous_modified = True
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            if wrd.code[j] != "":
                                                wrd.code[j] = ""
                                                conjunction_cleared = True
                                    elif last_char == "-":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                        previous_modified = True
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            if wrd.code[j] != "":
                                                wrd.code[j] = ""
                                                conjunction_cleared = True
                        else:
                            # Last char is consonant
                            if length == 2 and is_consonant_plus_consonant(remove_araab(pwrd.word)):
                                # 2-char consonant+consonant words: set code to "xx" and clear current word codes
                                pwrd.code[k] = "xx"
                                previous_modified = True
                                # Clear all codes in current word ("و")
                                for j in range(len(wrd.code)):
                                    if wrd.code[j] != "":
                                        wrd.code[j] = ""
                                        conjunction_cleared = True
                            else:
                                # Otherwise: modify code and clear current word codes
                                if len(pwrd.code[k]) > 0:
                                    last_char = pwrd.code[k][-1]
                                    if last_char == "=" or last_char == "x":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "-x"
                                        previous_modified = True
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            if wrd.code[j] != "":
                                                wrd.code[j] = ""
                                                conjunction_cleared = True
                                    elif last_char == "-":
                                        pwrd.code[k] = pwrd.code[k][:-1] + "x"
                                        previous_modified = True
                                        # Clear all codes in current word ("و")
                                        for j in range(len(wrd.code)):
                                            if wrd.code[j] != "":
                                                wrd.code[j] = ""
                                                conjunction_cleared = True
                    
                    # Log Ataf rule application (after all modifications)
                    if previous_modified or conjunction_cleared:
                        if previous_modified:
                            pwrd.prosodic_transformation_steps.append("ADJUSTED_PREVIOUS_WORD_CODE_FOR_CONJUNCTION_ATAF")
                        if conjunction_cleared:
                            wrd.prosodic_transformation_steps.append("CLEARED_SCANSION_CODES_FOR_CONJUNCTION_AFTER_MERGE")

                        explain_logger = get_explain_logger()
                        old_code_str = original_codes[0] if original_codes else 'none'
                        new_code_str = pwrd.code[0] if pwrd.code and pwrd.code[0] else 'none'
                        explain_logger.info(f"RULE | Ataf | Applied to Word {i} ('و') | Modified Word {i-1}: '{old_code_str}' → '{new_code_str}', cleared Word {i} codes")
    
    @staticmethod
    def process_word_grafting(line: 'Lines') -> None:
        """
        Process word grafting logic (وصال الف).
        
        Create taqti_word_graft codes when word starts with 'ا' or 'آ' following a consonant.
        Extracted from match_line_to_meters() lines 1477-1501.
        
        Args:
            line: Lines instance to process (modified in-place)
        """
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
                        
                        # Log word grafting rule application (after graft codes created)
                        if prev_word.taqti_word_graft:
                            prev_word.prosodic_transformation_steps.append("GRAFTED_WITH_FOLLOWING_VOWEL_INITIAL_WORD")
                            explain_logger = get_explain_logger()
                            graft_codes_str = ', '.join(prev_word.taqti_word_graft)
                            explain_logger.info(f"RULE | Word grafting | Applied to Word {i} ('{wrd.word}') | Created graft codes for Word {i-1}: {graft_codes_str}")

    @staticmethod
    def process_final_vowel_weakening(line: 'Lines') -> None:
        """
        Process final vowel weakening (حذفِ علتِ آخر).

        Allows optional weakening of a word-final long vowel
        (ے / ی / و) when followed by a light word and no pause.

        This rule is NON-DESTRUCTIVE:
        it adds alternative codes using 'x' instead of overwriting.
        """

        for i in range(len(line.words_list) - 1):
            wrd = line.words_list[i]
            next_wrd = line.words_list[i + 1]

            # --- basic guards ---
            if not wrd.code:
                continue

            stripped = remove_araab(wrd.word)
            if not stripped:
                continue

            last_char = stripped[-1]

            # --- only final long vowels ---
            if last_char not in ['ے', 'ی', 'و']:
                continue

            # --- do NOT weaken before auxiliaries (length must be preserved) ---
            if next_wrd.word in ['ہے', 'ہوں', 'تھا', 'تھی', 'تھے']:
                continue

            # --- do NOT interfere with word grafting (handled elsewhere) ---
            if next_wrd.word and next_wrd.word[0] in ['ا', 'آ']:
                continue

            weakening_applied = False

            # --- add flexible alternatives ---
            for code in list(wrd.code):  # iterate over a copy
                if not code:
                    continue

                # already flexible → nothing to do
                if code.endswith("x"):
                    continue

                weakened = None

                if code.endswith("=="):
                    weakened = code[:-2] + "=x"
                elif code.endswith("="):
                    weakened = code[:-1] + "x"

                if weakened and weakened not in wrd.code:
                    wrd.code.append(weakened)
                    weakening_applied = True

            # --- logging / explanation ---
            if weakening_applied:
                wrd.prosodic_transformation_steps.append(
                    "OPTIONAL_FINAL_VOWEL_WEAKENING_APPLIED"
                )

                explain_logger = get_explain_logger()
                explain_logger.info(
                    f"RULE | Final vowel weakening | "
                    f"Applied to Word {i} ('{wrd.word}') "
                    f"before '{next_wrd.word}'"
                )
