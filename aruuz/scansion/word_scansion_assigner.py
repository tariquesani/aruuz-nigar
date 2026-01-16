"""
Word Scansion Assigner Service

Service class for assigning scansion codes to words.
Handles database lookup, heuristics fallback, and compound word splitting.
"""

from typing import Optional

from aruuz.database.word_lookup import WordLookup
from aruuz.utils.araab import remove_araab
from aruuz.models import Words
from .code_assignment import compute_scansion
from .length_scanners import length_two_scan
from .explain_logging import get_explain_logger


class WordScansionAssigner:
    """
    Service class for word code assignment.
    
    Handles:
    - Database lookup (Strategy 1)
    - Heuristics fallback (Strategy 2)
    - Compound word splitting (Strategy 3)
    """
    
    def __init__(self, word_lookup: Optional[WordLookup] = None):
        """
        Initialize WordScansionAssigner.
        
        Args:
            word_lookup: Optional WordLookup instance for database access
        """
        self.word_lookup = word_lookup
    
    def assign_code_to_word(self, word: Words) -> Words:
        """
        Assign scansion code to a word in-place using database lookup (if available) or heuristics.
        
        This method:
        1. Tries database lookup first (if available)
        2. Falls back to heuristics using the compute_scansion function
        3. If heuristics fail (empty code) and word length > 4, tries compound word splitting
        
        Args:
            word: Words object to assign code to
            
        Returns:
            Words object with code assigned
        """
        # If word already has codes, return as is
        if len(word.code) > 0:
            word.assignment_method = "already_assigned"
            return word
        
        # Initialize tracking properties
        word.db_lookup_successful = False
        word.fallback_used = False
        
        # Strategy 1: Try database lookup first (if available)
        if self.word_lookup is not None:
            try:
                word = self.word_lookup.find_word(word)
                
                # If database lookup found results
                if len(word.id) > 0:
                    word.db_lookup_successful = True
                    # Apply special 3-character word handling
                    word = self._apply_db_variations(word)
                    # Log successful code assignment from database
                    if len(word.code) > 0:
                        word.assignment_method = "database"
                        # Append assignment summary step
                        word.scansion_generation_steps.append(f"ASSIGNED_CODE_CANDIDATES_DATABASE:count={len(word.code)}")
                        explain_logger = get_explain_logger()
                        codes_str = ', '.join(word.code)
                        explain_logger.info(f"RULE | Word ('{word.word}') | Assigned code '{codes_str}' | Source: database")
                    return word
            except Exception:
                # On any DB error, fall back to heuristics
                word.fallback_used = True
                pass
        
        # Strategy 2: Fallback to heuristics
        if not word.db_lookup_successful:
            word.fallback_used = True
        code = compute_scansion(word)
        
        # Strategy 3: Try compound word splitting if heuristics failed
        # C#: if (stripped.Length > 4 && code.Equals(""))
        stripped = remove_araab(word.word)
        if len(stripped) > 4 and code == "":
            # Try compound word splitting
            word_result = self._split_compound_word(word)
            # If compound_word found a valid split (has codes), use it
            if len(word_result.code) > 0:
                word_result.assignment_method = "compound_split"
                word_result.fallback_used = True  # Compound splitting is a fallback
                # Append assignment summary step
                word_result.scansion_generation_steps.append(f"ASSIGNED_CODE_CANDIDATES_COMPOUND_SPLIT:count={len(word_result.code)}")
                # Log successful code assignment from compound word splitting
                explain_logger = get_explain_logger()
                codes_str = ', '.join(word_result.code)
                explain_logger.info(f"RULE | Word ('{word_result.word}') | Assigned code '{codes_str}' | Source: compound word splitting")
                return word_result
            # Otherwise, continue with empty code (will be stored below)
        
        # Store code in word
        word.code = [code]
        
        # Set assignment method for heuristic path
        if word.assignment_method is None:
            word.assignment_method = "heuristic"
        
        # Log successful code assignment from heuristics (only if code is non-empty)
        if code:
            # Append assignment summary step
            word.scansion_generation_steps.append(f"ASSIGNED_SCANSION_CODE_HEURISTIC:code={code}")
            explain_logger = get_explain_logger()
            explain_logger.info(f"RULE | Word ('{word.word}') | Assigned code '{code}' | Source: heuristic")
        
        return word
    
    def _apply_db_variations(self, word: Words) -> Words:
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
                        # Append step for 3-letter variation rule
                        word.scansion_generation_steps.append("APPLIED_3_LETTER_DB_VARIATION_RULE_EQ_EQ")
                else:  # First character is not alif madd
                    # C#: if (!wrd.code[0].Equals("-=") && !wrd.code[0].Equals("-x"))
                    if len(word.code) > 0 and word.code[0] != "-=" and word.code[0] != "-x":
                        # C#: wrd.id.Add(-1);
                        # C#: wrd.code.Add("-=");
                        word.id.append(-1)
                        word.code.append("-=")
                        # Append step for 3-letter variation rule
                        word.scansion_generation_steps.append("APPLIED_3_LETTER_DB_VARIATION_RULE_MINUS_EQ")
        
        return word
    
    def _plural_form(self, substr: str, len_param: int) -> Words:
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
    
    def _plural_form_noon_ghunna(self, substr: str) -> Words:
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
    
    def _plural_form_aat(self, substr: str) -> Words:
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
    
    def _plural_form_aan(self, substr: str) -> Words:
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
    
    def _plural_form_ye(self, substr: str) -> Words:
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
    
    def _plural_form_postfix_aan(self, substr: str) -> Words:
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
    
    def _split_compound_word(self, wrd: Words) -> Words:
        """
        Attempt to split a word into compound parts and combine their codes.
        
        This method tries to split a word at various positions and:
        1. Uses find_word() on the first part (database lookup)
        2. Uses assign_code_to_word() on the second part (heuristics)
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
            # Use assign_code_to_word() on second part (heuristics)
            second = self.assign_code_to_word(second)
            
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
                # Set compound split position
                first.compound_split_position = i
                
                # Append compound split steps (using original word parts before combination)
                first_part = stripped[:i]
                second_part = stripped[i:]
                first.scansion_generation_steps.append(f"COMPOUND_SPLIT_SUCCEEDED:first_part={first_part},second_part={second_part},i={i}")
                first.scansion_generation_steps.append(f"COMBINED_CODES_FROM_SPLIT_PARTS:count={len(codes)}")
                
                # Add trace message for compound word split
                # Each part has its own trace from assign_code_to_word, parent records split decision
                first.scan_trace_steps.append(f"COMPOUND_WORD_SPLIT: split_pos={i}")
                first.scan_trace_steps.append(f"COMPOUND_WORD_PARTS: first={first_part},second={second_part}")
                
                wd = first
                break
        
        # Set modified flag (matching C#: wd.modified = true)
        wd.modified = True
        return wd
