"""
Explanation Builder for User-Facing Scansion Explanations

This module provides the ExplanationBuilder class that converts technical
scansion trace information into user-friendly explanations.
"""

from typing import Dict, Any, Optional, List, Union
from aruuz.models import Words


# Identifier-to-explanation mappings for scansion_generation_steps
# These mappings convert technical identifiers to user-friendly explanations.
# Values are format strings that can be formatted with parameters extracted from identifiers.
# Parameters like :count=X, :scanner=X, etc. will be parsed and used to format these templates.
IDENTIFIER_MAPPINGS: Dict[str, str] = {
    # Database assignment identifiers
    # Format: "ASSIGNED_CODE_CANDIDATES_DATABASE:count=X"
    "ASSIGNED_CODE_CANDIDATES_DATABASE": "",
    # Format: "ASSIGNED_CODE_CANDIDATES_COMPOUND_SPLIT:count=X"
    "ASSIGNED_CODE_CANDIDATES_COMPOUND_SPLIT": "Word was split into compound parts, resulting in {count} code variation{plural}",
    # Format: "ASSIGNED_SCANSION_CODE_HEURISTIC:code=X"
    "ASSIGNED_SCANSION_CODE_HEURISTIC": "Code '{code}' was assigned using heuristic analysis",
    
    # Length-based scan identifiers - all map to generic heuristic analysis (NOT exposing function names)
    # These should NEVER expose function names like "length_five_scan" to users
    "APPLIED_LENGTH_ONE_SCAN": "Analyzed using heuristic analysis",
    "APPLIED_LENGTH_TWO_SCAN": "Analyzed using heuristic analysis",
    "APPLIED_LENGTH_THREE_SCAN": "Analyzed using heuristic analysis",
    "APPLIED_LENGTH_FOUR_SCAN": "Analyzed using heuristic analysis",
    "APPLIED_LENGTH_FIVE_SCAN": "Analyzed using heuristic analysis",
    
    # Heuristic scanner identifier - generic description (scanner name will be stripped)
    # Format: "APPLIED_HEURISTIC_SCANNER_USED:scanner=X"
    # The scanner parameter will be ignored/stripped to hide technical function names
    "APPLIED_HEURISTIC_SCANNER_USED": "Analyzed using heuristic analysis",
    
    # Taqti-based segmentation
    # Format: "USED_TAQTI_BASED_HEURISTIC_SEGMENTATION:count=X"
    "USED_TAQTI_BASED_HEURISTIC_SEGMENTATION": "Word was segmented into {count} part{plural} based on taqti",
    
    # Database variation rules
    "APPLIED_3_LETTER_DB_VARIATION_RULE_EQ_EQ": "Applied special 3-character word variation rule",
    "APPLIED_3_LETTER_DB_VARIATION_RULE_MINUS_EQ": "Applied special 3-character word variation rule",
    
    # Word-final rules
    "APPLIED_WORD_FINAL_VOWEL_H_RULE": "Applied word-final flexible syllable rule",
    
    # Compound word splitting
    # Format: "COMPOUND_SPLIT_SUCCEEDED:first_part=X,second_part=Y,i=Z"
    "COMPOUND_SPLIT_SUCCEEDED": "Compound word was successfully split into '{first_part}' and '{second_part}' at position {i}",
    # Format: "COMBINED_CODES_FROM_SPLIT_PARTS:count=X"
    "COMBINED_CODES_FROM_SPLIT_PARTS": "Codes from split parts were combined, resulting in {count} code variation{plural}",
    
    # Additional database lookup identifiers (from word_lookup.py)
    # These may appear in scansion_generation_steps if database lookup succeeds
    "FOUND_IN_DATABASE_EXCEPTIONS_TABLE": "in exceptions table with code,",
    "FOUND_IN_DATABASE_MASTERTABLE": "",
    "FOUND_IN_DATABASE_PLURALS_TABLE": "Word was found in database plurals table",
    "FOUND_IN_DATABASE_VARIATIONS_TABLE": "Word was found in database variations table",
    "COMPUTED_CODE_FROM_DATABASE_TAQTI": "",
}


# Prefix patterns to strip from scan_trace_steps identifiers
# These prefixes (like L1S|, L2S|, etc.) are technical function markers that should be hidden from users
TRACE_PREFIX_PATTERNS: List[str] = [
    "L1S| ",
    "L2S| ",
    "L3S| ",
    "L4S| ",
    "L5S| ",
    # Also handle variations without trailing space
    "L1S|",
    "L2S|",
    "L3S|",
    "L4S|",
    "L5S|",
]


# Identifier-to-explanation mappings for scan_trace_steps (after prefix removal)
# These mappings convert technical trace identifiers to user-friendly explanations.
# Values are format strings that can be formatted with parameters extracted from identifiers.
# Parameters like start_pos=X, end_pos=Y, etc. will be parsed and used to format these templates.
TRACE_IDENTIFIER_MAPPINGS: Dict[str, str] = {
    # Input processing identifiers - these are internal details, typically filtered out
    # but kept here for completeness in case include_technical=True is used
    "INPUT_SUBSTRING": "",  # Filtered out (internal detail)
    "AFTER_REMOVING_HAY_AND_NUN": "",  # Filtered out (internal detail)
    "AFTER_REMOVING_ARAAB_STRIPPED": "",  # Filtered out (internal detail)
    
    # Pattern detection identifiers - these are meaningful to users
    # Format: "DETECTED_ASPIRATED_YEH_PATTERN: start_pos=X,end_pos=Y"
    "DETECTED_ASPIRATED_YEH_PATTERN": "Detected aspirated character (ھ) followed by ی at positions {start_pos}-{end_pos}, which forces a specific vowel pattern",
    # Format: "DETECTED_ALIF_MADD: return_code=X"
    "DETECTED_ALIF_MADD": "Detected alif madd (آ) pattern",
    "NO_ALIF_MADD": "No alif madd pattern detected",
    "DETECTED_ALIF_MADD_START": "Detected alif madd (آ) at the start",
    "DETECTED_VOWEL_PLUS_H_END": "Detected vowel followed by h (ہ) at the end",
    # Format: "DETECTED_ALIF: position=X"
    "DETECTED_ALIF": "Detected alif at position {position}",
    "ALIF_POSITION_DETECTED": "Detected alif at position {position}",
    # Format: "VOWEL_POSITION_DETECTED: position=X,char=Y"
    "VOWEL_POSITION_DETECTED": "Detected vowel '{char}' at position {position}",
    # Format: "DIACRITIC_DETECTED: diacritic=X"
    "DIACRITIC_DETECTED": "Detected diacritic mark ({diacritic})",
    
    # Word classification identifiers
    "WORD_IS_MUARRAB": "Word has diacritic marks (muarrab)",
    "WORD_NOT_MUARRAB": "Word has no diacritic marks (non-muarrab)",
    "ENTERING_MUARRAB_BRANCH": "Analyzing word with diacritic marks",
    "ENTERING_NON_MUARRAB_BRANCH": "Analyzing word without diacritic marks",
    "LOCATED_DIACRITICS": "Located {positions} diacritic mark(s) in the word",
    
    # Pattern matching identifiers - these explain the reasoning
    # Format: "PATTERN_MATCHED: diacritic=X,code=Y" or "PATTERN_MATCHED: pattern=X,code=Y"
    "PATTERN_MATCHED": "Pattern matched: {pattern_details}",
    "NO_PATTERN_MATCHED": "No specific pattern matched, using default rule",
    "PATTERN_CHECK_1": "Checking pattern condition 1",
    "PATTERN_CHECK_2": "Checking pattern condition 2",
    "PATTERN_CHECK_3": "Checking pattern condition 3",
    "PATTERN_CHECK_4": "Checking pattern condition 4",
    "PATTERN_CHECK_5": "Checking pattern condition 5",
    "PATTERN_CHECK_6": "Checking pattern condition 6",
    "PATTERN_CHECK_7": "All previous pattern checks failed",
    "DEFAULT_PATTERN": "Using default pattern",
    
    # Character/position checking identifiers
    # Format: "CHECKING_CHARACTER_AT_POSITION: pos=X,character=Y"
    "CHECKING_CHARACTER_AT_POSITION": "Checking character '{character}' at position {pos}",
    # Format: "CHECKING_DIACRITIC_AT_POSITION: pos=X,diacritic=Y,character=Z"
    "CHECKING_DIACRITIC_AT_POSITION": "Checking diacritic mark ({diacritic}) at position {pos}",
    # Format: "CHECKING_VOWEL_AT_POSITION: pos=X,character=Y"
    "CHECKING_VOWEL_AT_POSITION": "Checking vowel '{character}' at position {pos}",
    "CHECKING_SUB_CONDITION": "Checking additional condition",
    "CHECKING_CHARACTER_PATTERN": "Checking character pattern",
    
    # Delegation and splitting identifiers
    # Format: "STRIPPED_LENGTH_DELEGATE: length=X,delegate_to=Y"
    "STRIPPED_LENGTH_DELEGATE": "Delegated to shorter length analysis",
    "STRIPPED_LENGTH_1_ALIF_MADD": "After stripping, length 1 with alif madd",
    "STRIPPED_LENGTH_1_NO_ALIF_MADD": "After stripping, length 1 without alif madd",
    # Format: "SPLIT_AT_POSITION: split_pos=X,delegate_to=Y,remaining=Z"
    "SPLIT_AT_POSITION": "Split word at position {split_pos} for analysis",
    # Format: "SPLIT_DECISION: split_pos=X,reason=Y,remaining=Z"
    "SPLIT_DECISION": "Decided to split word at position {split_pos}",
    
    # Compound word identifiers
    # Format: "COMPOUND_WORD_SPLIT: split_pos=X"
    "COMPOUND_WORD_SPLIT": "Compound word was split at position {split_pos}",
    # Format: "COMPOUND_WORD_PARTS: first=X,second=Y"
    "COMPOUND_WORD_PARTS": "Split into parts: '{first}' and '{second}'",
    
    # Special pattern identifiers
    "MUARRAB_PATH_ALIF_DETECTED": "Checking for alif patterns in diacritically marked word",
    "MUARRAB_PATH_VOWEL_DETECTED": "Checking for vowel patterns (و/ی) in diacritically marked word",
    "EARLY_RETURN_ASPIRATED_YEH_PATTERN": "Early return due to aspirated yeh pattern",
    
    # Adjustment identifiers
    # Format: "APPLIED_NOON_GHUNNA_ADJUSTMENT: old_code=X,new_code=Y"
    "APPLIED_NOON_GHUNNA_ADJUSTMENT": "Applied noon ghunna adjustment: changed code from '{old_code}' to '{new_code}'",
    
    # Return identifiers
    # Format: "RETURNING: code=X"
    "RETURNING": "Final scansion code determined",
}


# Identifier-to-explanation mappings for prosodic_transformation_steps
# These mappings convert technical prosodic transformation identifiers to user-friendly explanations.
# Prosodic transformations are post-scansion adjustments that modify codes based on context
# (Al prefix, Izafat, Ataf, Word Grafting).
PROSODIC_MAPPINGS: Dict[str, str] = {
    # Al (ال) prefix transformations
    # When current word is extended to absorb following 'ال' prefix
    "EXTENDED_PREVIOUS_WORD_TO_ABSORB_AL": "Extended previous word to absorb Al (ال) prefix",
    # When Al prefix is merged with previous word
    "MERGED_AL_WITH_PREVIOUS_WORD": "Merged Al (ال) prefix with previous word",
    
    # Izafat (اضافت) transformations
    # When possessive marker adjustment is applied to final syllable
    "APPLIED_IZAFAT_ADJUSTMENT_TO_FINAL_SYLLABLE": "Applied Izafat adjustment to final syllable",
    
    # Ataf (عطف) transformations
    # When previous word's code is adjusted for conjunction "و"
    "ADJUSTED_PREVIOUS_WORD_CODE_FOR_CONJUNCTION_ATAF": "Adjusted previous word code for conjunction (و)",
    # When conjunction word's codes are cleared after merge
    "CLEARED_SCANSION_CODES_FOR_CONJUNCTION_AFTER_MERGE": "Cleared scansion codes for conjunction after merge",
    
    # Word grafting transformations
    # When word is grafted with following word starting with vowel
    "GRAFTED_WITH_FOLLOWING_VOWEL_INITIAL_WORD": "Grafted with following word starting with vowel",
}


# Template dictionary for building user-friendly explanations
# These templates are used to format common explanation patterns with variable substitution
TEMPLATES: Dict[str, str] = {
    "database_found": "Word '{word}' was found in database",
    "with_taqti": "with taqti '{taqti}'",
    "processed_as": "This was processed as {code}",
    "because": "because {reason}",
    "heuristic_used": "Word '{word}' was analyzed using heuristic analysis",
    "compound_split": "Word '{word}' was split at position {pos}",
    "resulting_code": "resulting in code '{code}'",
    "resulting_codes": "resulting in codes: {codes}",
    "transformation_applied": "After base scansion, {transformation} was applied",
    "multiple_codes": "Word '{word}' has {count} possible scansion codes",
    "no_trace_available": "No detailed analysis trace available",
    "missing_information": "Word '{word}' was processed, but detailed trace information is not available.",
}


class ExplanationBuilder:
    """
    Builds user-friendly explanations from technical scansion trace data.
    
    Converts identifier-based trace messages (e.g., from scansion_generation_steps,
    scan_trace_steps, prosodic_transformation_steps) into readable explanations
    that hide technical implementation details like function names.
    
    Attributes:
        language: Language code for explanations (default: "en")
        word: The Words object being explained
        parts: List of explanation text parts (for string format)
        structured: Dictionary of structured explanation data
    """
    
    @staticmethod
    def _strip_function_prefix(identifier: str) -> str:
        """
        Strip function name prefixes (L1S|, L2S|, etc.) from trace identifiers.
        
        Args:
            identifier: The trace identifier string (e.g., "L5S| DETECTED_ASPIRATED_YEH_PATTERN: start_pos=2")
        
        Returns:
            Identifier with prefix removed (e.g., "DETECTED_ASPIRATED_YEH_PATTERN: start_pos=2")
        """
        for prefix in TRACE_PREFIX_PATTERNS:
            if identifier.startswith(prefix):
                return identifier[len(prefix):].lstrip()
        return identifier
    
    @staticmethod
    def _parse_identifier_params(identifier: str) -> Dict[str, str]:
        """
        Parse key=value parameters from identifier string.
        
        Extracts parameters in the format "IDENTIFIER: key1=value1,key2=value2" or
        "IDENTIFIER: key1=value1, key2=value2" (with spaces after colon or commas).
        
        Args:
            identifier: The identifier string (e.g., "ASSIGNED_CODE_CANDIDATES_DATABASE:count=5"
                        or "DETECTED_ASPIRATED_YEH_PATTERN: start_pos=2,end_pos=3")
        
        Returns:
            Dictionary of parameter key-value pairs (e.g., {"count": "5"} or
            {"start_pos": "2", "end_pos": "3"}). Returns empty dict if no parameters found.
        
        Examples:
            >>> ExplanationBuilder._parse_identifier_params("IDENTIFIER:count=5")
            {'count': '5'}
            >>> ExplanationBuilder._parse_identifier_params("IDENTIFIER: start_pos=2,end_pos=3")
            {'start_pos': '2', 'end_pos': '3'}
            >>> ExplanationBuilder._parse_identifier_params("IDENTIFIER")
            {}
        """
        params: Dict[str, str] = {}
        
        # Split on colon to separate identifier from parameters
        if ':' not in identifier:
            return params
        
        param_string = identifier.split(':', 1)[1].strip()
        if not param_string:
            return params
        
        # Parse key=value pairs separated by commas
        # Handle both "key=value,key2=value2" and "key=value, key2=value2" formats
        pairs = [pair.strip() for pair in param_string.split(',')]
        
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key.strip()] = value.strip()
        
        return params
    
    @staticmethod
    def _format_template(template_key: str, **kwargs: Any) -> str:
        """
        Format a template string with provided keyword arguments.
        
        Args:
            template_key: Key to look up in TEMPLATES dictionary
            **kwargs: Keyword arguments to substitute into the template
        
        Returns:
            Formatted string with variables substituted, or empty string if template key not found
        
        Examples:
            >>> ExplanationBuilder._format_template("database_found", word="کتاب")
            "Word 'کتاب' was found in database"
            >>> ExplanationBuilder._format_template("resulting_code", code="1221")
            "resulting in code '1221'"
            >>> ExplanationBuilder._format_template("nonexistent_key")
            ""  # Returns empty string for missing template key
        """
        if template_key not in TEMPLATES:
            # Template key not found - return empty string gracefully
            return ""
        
        template = TEMPLATES[template_key]
        
        try:
            # Format template with provided keyword arguments
            formatted = template.format(**kwargs)
            return formatted
        except (KeyError, ValueError):
            # Template formatting failed (missing parameters or format error)
            # Return template as-is if it has no placeholders, or empty string
            if '{' not in template and '}' not in template:
                return template
            # Template has placeholders but formatting failed - return empty string
            return ""
    
    @staticmethod
    def _map_identifier(identifier: str, mapping_type: str) -> str:
        """
        Map identifier to user-friendly explanation using appropriate mapping dictionary.
        
        Args:
            identifier: The identifier string (may include parameters like "IDENTIFIER:count=5")
            mapping_type: Type of mapping to use - "generation", "trace", or "prosodic"
        
        Returns:
            User-friendly explanation string, or empty string if identifier is filtered out,
            or the original identifier if no mapping found and it's not filtered.
        
        Examples:
            >>> ExplanationBuilder._map_identifier("APPLIED_LENGTH_FIVE_SCAN", "generation")
            "Analyzed using heuristic analysis"
            >>> ExplanationBuilder._map_identifier("ASSIGNED_CODE_CANDIDATES_DATABASE:count=3", "generation")
            "Word was found in database with 3 code variations"
            >>> ExplanationBuilder._map_identifier("INPUT_SUBSTRING: substr=test", "trace")
            ""  # Filtered out as internal detail
        """
        # Split identifier and parameters
        base_identifier = identifier.split(':')[0].strip()
        params = ExplanationBuilder._parse_identifier_params(identifier)
        
        # Select appropriate mapping dictionary based on mapping_type
        if mapping_type == "generation":
            mapping_dict = IDENTIFIER_MAPPINGS
        elif mapping_type == "trace":
            mapping_dict = TRACE_IDENTIFIER_MAPPINGS
        elif mapping_type == "prosodic":
            mapping_dict = PROSODIC_MAPPINGS
        else:
            # Unknown mapping type - return original identifier
            return identifier
        
        # Look up base identifier in mapping dictionary
        if base_identifier not in mapping_dict:
            # No mapping found - return original identifier
            return identifier
        
        template = mapping_dict[base_identifier]
        
        # If template is empty string, this identifier should be filtered out
        if not template:
            return ""
        
        # Format template with parameters if it contains placeholders
        try:
            # Handle plural forms (e.g., "{count} code variation{plural}")
            if 'plural' in template and 'count' in params:
                count_val = params.get('count', '1')
                try:
                    count = int(count_val)
                    params['plural'] = 's' if count != 1 else ''
                except (ValueError, TypeError):
                    params['plural'] = 's'
            
            # Special handling for PATTERN_MATCHED - construct pattern_details from available params
            if base_identifier == "PATTERN_MATCHED" and 'pattern_details' in template:
                pattern_parts = []
                if 'diacritic' in params:
                    diacritic = params['diacritic']
                    # Clean up diacritic description
                    diacritic_clean = diacritic.replace('_', ' ').replace('at pos', 'at position')
                    pattern_parts.append(f"diacritic mark ({diacritic_clean})")
                if 'code' in params:
                    code = params['code']
                    pattern_parts.append(f"determines code '{code}'")
                if 'pattern' in params:
                    pattern = params['pattern']
                    pattern_parts.append(f"pattern: {pattern}")
                
                if pattern_parts:
                    params['pattern_details'] = ", ".join(pattern_parts)
                else:
                    # Fallback: use code if available, or generic message
                    if 'code' in params:
                        params['pattern_details'] = f"determines code '{params['code']}'"
                    else:
                        params['pattern_details'] = "pattern matched"
            
            # Format template with all available parameters
            formatted = template.format(**params)
            return formatted
        except (KeyError, ValueError):
            # Template formatting failed (missing parameters or format error)
            # Return template as-is if it has no placeholders, or original identifier
            if '{' not in template and '}' not in template:
                return template
            # Template has placeholders but formatting failed - return original identifier
            return identifier
    
    def __init__(self, language: str = "en"):
        """
        Initialize the ExplanationBuilder.
        
        Args:
            language: Language code for explanations (default: "en")
        """
        self.language: str = language
        self.word: Optional[Words] = None
        self.parts: List[str] = []
        self.structured: Dict[str, Any] = {}
    
    def add_summary(self) -> None:
        """
        Add one-line summary overview based on assignment method.
        
        Generates a summary based on how the word was processed:
        - Database lookup: "Word '{word}' was found in database"
        - Heuristic analysis: "Word '{word}' was analyzed using heuristic analysis"
        - Compound split: "Word '{word}' was split at position {pos}"
        - Already assigned: "Word '{word}' was previously assigned"
        
        Stores summary in both self.parts (for string format) and
        self.structured["summary"] (for structured format).
        """
        if not self.word:
            return
        
        summary_text = ""
        
        # Handle missing information edge case (Phase 4.4) - ensure word.word exists
        word_text = self.word.word if self.word.word else "word"
        
        # Priority order: database lookup first, then heuristic, then compound_split, then already_assigned
        # Handle compound words edge case (Phase 4.3) - check for compound split identifiers
        is_compound_split = False
        compound_parts = None
        split_pos = None
        
        # First, try to detect compound split from trace identifiers
        if self.word.scansion_generation_steps:
            for identifier in self.word.scansion_generation_steps:
                base_id = identifier.split(':')[0].strip()
                if base_id == "COMPOUND_SPLIT_SUCCEEDED":
                    is_compound_split = True
                    # Extract parts from identifier parameters
                    params = self._parse_identifier_params(identifier)
                    if "first_part" in params and "second_part" in params:
                        compound_parts = (params["first_part"], params["second_part"])
                    if "i" in params:
                        try:
                            split_pos = int(params["i"])
                        except (ValueError, TypeError):
                            pass
                    break
        
        # Also check scan_trace_steps for COMPOUND_WORD_SPLIT
        if not is_compound_split and self.word.scan_trace_steps:
            for identifier in self.word.scan_trace_steps:
                stripped_id = self._strip_function_prefix(identifier)
                base_id = stripped_id.split(':')[0].strip()
                if base_id == "COMPOUND_WORD_SPLIT":
                    is_compound_split = True
                    params = self._parse_identifier_params(stripped_id)
                    if "split_pos" in params:
                        try:
                            split_pos = int(params["split_pos"])
                        except (ValueError, TypeError):
                            pass
                    break
        
        # Use detected compound split info or fall back to assignment_method
        if is_compound_split or self.word.assignment_method == "compound_split":
            # Word was split into compound parts (Phase 4.3)
            if split_pos is not None:
                summary_text = self._format_template(
                    "compound_split",
                    word=word_text,
                    pos=split_pos
                )
            elif compound_parts:
                summary_text = f"Word '{word_text}' was split into compound parts: '{compound_parts[0]}' and '{compound_parts[1]}'"
            elif self.word.compound_split_position is not None:
                summary_text = self._format_template(
                    "compound_split",
                    word=word_text,
                    pos=self.word.compound_split_position
                )
            else:
                # Fallback if split position is not available
                summary_text = f"Word '{word_text}' was split into compound parts"
        elif self.word.db_lookup_successful:
            # Word was found in database
            summary_text = self._format_template("database_found", word=word_text)
        elif self.word.assignment_method == "heuristic" or self.word.heuristic_scanner_used:
            # Word was analyzed using heuristic analysis (do NOT expose function names)
            summary_text = self._format_template("heuristic_used", word=word_text)
        elif self.word.assignment_method == "already_assigned":
            # Word was previously assigned (e.g., from input or previous processing)
            summary_text = f"Word '{word_text}' was previously assigned"
        
        # Store summary if we generated one
        if summary_text:
            self.parts.append(summary_text)
            self.structured["summary"] = summary_text
    
    def add_method(self) -> None:
        """
        Add method description (without technical function names).
        
        Maps word.assignment_method to user-friendly description:
        - "database" → "database lookup"
        - "heuristic" → "heuristic analysis" (NOT "length_five_scan" or similar)
        - "compound_split" → "compound word splitting"
        - "already_assigned" → "previously assigned"
        
        Stores in self.structured["method"] (not in parts as it's part of summary).
        """
        if not self.word:
            return
        
        # Handle missing information edge case (Phase 4.4)
        # Map assignment_method to user-friendly description
        method_mapping: Dict[str, str] = {
            "database": "database lookup",
            "heuristic": "heuristic analysis",
            "compound_split": "compound word splitting",
            "already_assigned": "previously assigned",
        }
        
        assignment_method = self.word.assignment_method
        
        # Get user-friendly description from mapping, or use assignment_method as fallback
        method_description = method_mapping.get(assignment_method, assignment_method or "unknown method")
        
        # Store in structured dict (not in parts as it's part of summary)
        self.structured["method"] = method_description
    
    def add_taqti(self) -> None:
        """
        Add taqti information if available.
        
        Checks if word.taqti exists and has items, then adds "with taqti '{taqti}'"
        using the last taqti value. Stores the last taqti value in
        self.structured["taqti"] and all taqti values in
        self.structured["taqti_breakdown"].
        """
        if not self.word:
            return
        
        # Handle missing information edge case (Phase 4.4)
        # Check if taqti exists and has items
        if self.word.taqti and len(self.word.taqti) > 0:
            # Get the last taqti value (most recent/final)
            last_taqti = self.word.taqti[-1]
            
            # Format using template
            taqti_text = self._format_template("with_taqti", taqti=last_taqti)
            
            # Add to parts for string format
            if taqti_text:
                self.parts.append(taqti_text)
            
            # Store in structured format
            self.structured["taqti"] = last_taqti
            self.structured["taqti_breakdown"] = self.word.taqti.copy() if self.word.taqti else None
        else:
            # No taqti available - set to None in structured format
            self.structured["taqti"] = None
            self.structured["taqti_breakdown"] = None
    
    def add_steps(self) -> None:
        """
        Add formatted steps from scansion_generation_steps and scan_trace_steps.
        
        Merges, filters, translates, and orders steps from both trace fields:
        - Strips function prefixes (L1S|, L2S|, etc.) from scan_trace_steps
        - Maps identifiers to user-friendly explanations
        - Removes overly technical or redundant messages (like INPUT_SUBSTRING)
        - Parses identifier parameters to create contextual explanations
        - Orders steps logically (not chronologically)
        - Groups related steps into single explanations where appropriate
        
        Stores formatted steps in both self.parts (for string format) and
        self.structured["steps"] (for structured format).
        """
        if not self.word:
            return
        
        formatted_steps: List[str] = []
        
        # Handle missing/empty trace fields gracefully
        # Check if trace fields exist and are not None/empty
        has_generation_steps = (self.word.scansion_generation_steps is not None and 
                                len(self.word.scansion_generation_steps) > 0)
        has_trace_steps = (self.word.scan_trace_steps is not None and 
                          len(self.word.scan_trace_steps) > 0)
        
        # Process scansion_generation_steps (high-level strategy decisions)
        generation_steps: List[str] = []
        if has_generation_steps:
            for identifier in self.word.scansion_generation_steps:
                explanation = self._map_identifier(identifier, "generation")
                if explanation:  # Filter out empty strings (filtered identifiers)
                    generation_steps.append(explanation)
        
        # Process scan_trace_steps (detailed trace from length_*_scan functions)
        trace_steps: List[str] = []
        if has_trace_steps:
            for identifier in self.word.scan_trace_steps:
                # Strip function prefix first (L1S|, L2S|, etc.)
                stripped_identifier = self._strip_function_prefix(identifier)
                # Map using trace identifier mappings
                explanation = self._map_identifier(stripped_identifier, "trace")
                if explanation:  # Filter out empty strings (filtered identifiers)
                    trace_steps.append(explanation)
        
        # Merge and order steps logically
        # Priority order:
        # 1. Database-related steps (from generation_steps)
        # 2. Heuristic analysis steps (from generation_steps)
        # 3. Pattern detection and analysis steps (from trace_steps)
        # 4. Compound word splitting steps (from both)
        # 5. Other steps
        
        # Separate steps by category for logical ordering
        database_steps: List[str] = []
        heuristic_steps: List[str] = []
        pattern_steps: List[str] = []
        compound_steps: List[str] = []
        other_steps: List[str] = []
        
        # Categorize generation steps
        for step in generation_steps:
            step_lower = step.lower()
            if "database" in step_lower or "found in" in step_lower:
                database_steps.append(step)
            elif "compound" in step_lower or "split" in step_lower:
                compound_steps.append(step)
            elif "heuristic" in step_lower or "analyzed using" in step_lower:
                heuristic_steps.append(step)
            elif "variation rule" in step_lower or "flexible syllable" in step_lower:
                other_steps.append(step)
            else:
                other_steps.append(step)
        
        # Categorize trace steps
        for step in trace_steps:
            step_lower = step.lower()
            if "compound" in step_lower or "split" in step_lower:
                compound_steps.append(step)
            elif "detected" in step_lower or "pattern" in step_lower or "diacritic" in step_lower:
                pattern_steps.append(step)
            elif "analyzing" in step_lower or "checking" in step_lower:
                pattern_steps.append(step)
            elif "adjustment" in step_lower or "applied" in step_lower:
                other_steps.append(step)
            elif "final" in step_lower or "returning" in step_lower:
                # Skip final return messages as they're redundant
                continue
            else:
                other_steps.append(step)
        
        # Combine steps in logical order
        formatted_steps.extend(database_steps)
        formatted_steps.extend(heuristic_steps)
        formatted_steps.extend(pattern_steps)
        formatted_steps.extend(compound_steps)
        formatted_steps.extend(other_steps)
        
        # Filter out generic "Word was found in database" if we have specific table messages
        # Check if we have any specific table messages (exceptions, mastertable, plurals, variations)
        has_specific_table = any(
            "exceptions table" in step.lower() or 
            "mastertable" in step.lower() or 
            "plurals table" in step.lower() or 
            "variations table" in step.lower()
            for step in formatted_steps
        )
        
        # Also check if summary already mentions database lookup
        summary_mentions_database = (
            self.structured.get("summary", "").lower().count("found in database") > 0
        )
        
        # Filter out generic "Word was found in database" messages
        # (exact match without table name) if we have specific table info or summary mentions database
        if has_specific_table or summary_mentions_database:
            filtered_steps: List[str] = []
            for step in formatted_steps:
                step_lower = step.lower().strip()
                # Skip exact match "word was found in database" (generic, no table name)
                # But keep messages like "word was found in database with X code variation"
                # and "word was found in database exceptions table"
                if step_lower == "word was found in database":
                    continue
                filtered_steps.append(step)
            formatted_steps = filtered_steps
        
        # Remove duplicates while preserving order
        seen = set()
        unique_steps: List[str] = []
        for step in formatted_steps:
            if step not in seen:
                seen.add(step)
                unique_steps.append(step)
        
        # Handle edge case: empty traces (Phase 4.1)
        # If scan_trace_steps is empty but scansion_generation_steps exists, that's fine
        # (normal for database lookup path). Only add fallback if both are empty.
        if not unique_steps:
            # Check if we have any trace information at all
            if not has_generation_steps and not has_trace_steps:
                # No trace available - add fallback message
                fallback = self._format_template("no_trace_available")
                if fallback:
                    unique_steps.append(fallback)
        
        # Store formatted steps
        if unique_steps:
            # Add to parts for string format (join with periods and spaces for readability)
            steps_text = ". ".join(unique_steps)
            if steps_text:
                self.parts.append(steps_text)
            
            # Store in structured format
            self.structured["steps"] = unique_steps
        else:
            # No steps available
            self.structured["steps"] = []
    
    def add_code(self) -> None:
        """
        Add resulting scansion code(s) information.
        
        Checks if word.code has items, then formats appropriately:
        - If single code: adds "resulting in code '{code}'"
        - If multiple codes: adds "resulting in codes: {codes}" or formats as list
          and tries to explain why multiple codes exist if trace provides context
        
        Stores primary code (first code) in self.structured["code"] and
        all codes in self.structured["codes"]. Also adds formatted text to
        self.parts for string format.
        """
        if not self.word:
            return
        
        # Handle missing information edge case (Phase 4.4)
        # Check if code exists and has items
        if self.word.code and len(self.word.code) > 0:
            codes = self.word.code
            
            # Format code text based on number of codes
            if len(codes) == 1:
                # Single code
                single_code = codes[0]
                code_text = self._format_template("resulting_code", code=single_code)
                
                # Store in structured format
                self.structured["code"] = single_code
                self.structured["codes"] = codes.copy()
            else:
                # Multiple codes (Phase 4.2) - format as comma-separated list
                codes_str = ", ".join([f"'{code}'" for code in codes])
                
                # Try to explain why multiple codes exist if trace provides context
                # Check for variation-related identifiers in generation steps
                variation_reason = None
                if self.word.scansion_generation_steps:
                    for identifier in self.word.scansion_generation_steps:
                        base_id = identifier.split(':')[0].strip()
                        if "VARIATION" in base_id or "COMBINED_CODES" in base_id:
                            # Extract count if available
                            params = self._parse_identifier_params(identifier)
                            if "count" in params:
                                count = params["count"]
                                variation_reason = f"Word has {count} code variation{'s' if count != '1' else ''} due to different interpretation options"
                            break
                
                if variation_reason:
                    # Use template with explanation
                    code_text = f"{variation_reason}, resulting in codes: {codes_str}"
                else:
                    # Default format
                    code_text = self._format_template("resulting_codes", codes=codes_str)
                
                # Store primary code (first one) and all codes
                self.structured["code"] = codes[0]
                self.structured["codes"] = codes.copy()
            
            # Add to parts for string format
            if code_text:
                self.parts.append(code_text)
        else:
            # No code available - set to None/empty in structured format
            self.structured["code"] = None
            self.structured["codes"] = []
    
    def add_transformations(self) -> None:
        """
        Add prosodic transformation steps information if available.
        
        Checks if word.prosodic_transformation_steps has items, then maps each
        transformation identifier using PROSODIC_MAPPINGS and formats them as:
        "After base scansion, the following adjustments were made: {transformations}"
        
        Shows base code before transformations and final code after transformations
        (Phase 4.5): "...resulting in base code '{code}'. After base scansion, {transformations}. Final code: '{final_code}'"
        
        Stores formatted transformations in both self.parts (for string format)
        and self.structured["transformations"] (for structured format).
        """
        if not self.word:
            return
        
        # Handle missing information edge case (Phase 4.4)
        # Check if prosodic_transformation_steps exists and has items
        if self.word.prosodic_transformation_steps and len(self.word.prosodic_transformation_steps) > 0:
            # Map each transformation identifier to user-friendly explanation
            formatted_transformations: List[str] = []
            
            for identifier in self.word.prosodic_transformation_steps:
                explanation = self._map_identifier(identifier, "prosodic")
                if explanation:  # Filter out empty strings (shouldn't happen for prosodic, but safe)
                    formatted_transformations.append(explanation)
            
            # Format transformations text (Phase 4.5)
            if formatted_transformations:
                # Join transformations with commas and "and" for the last one
                if len(formatted_transformations) == 1:
                    transformations_text = formatted_transformations[0]
                elif len(formatted_transformations) == 2:
                    transformations_text = f"{formatted_transformations[0]} and {formatted_transformations[1]}"
                else:
                    # Multiple transformations: "X, Y, and Z"
                    transformations_text = ", ".join(formatted_transformations[:-1])
                    transformations_text += f", and {formatted_transformations[-1]}"
                
                # Phase 4.5: Show base code before transformations and final code after
                # Try to determine if there's a base code vs final code difference
                base_code = None
                final_code = None
                
                # If we have codes, use the first one as base/final
                # In practice, the word.code might already reflect the transformation,
                # but we show it as the final code
                if self.word.code and len(self.word.code) > 0:
                    # For simplicity, use the primary code as final code
                    # The base code would ideally come from before transformations,
                    # but that information isn't stored separately, so we use the final code
                    final_code = self.word.code[0]
                    base_code = final_code  # Fallback: same code if we can't determine base
                
                # Build transformation text with base and final codes if available
                if base_code and final_code and base_code != final_code:
                    # Codes changed - show both
                    transformation_text = f"Base code was '{base_code}'. After base scansion, {transformations_text.lower()}. Final code: '{final_code}'"
                elif final_code:
                    # Only final code available (most common case)
                    transformation_text = f"After base scansion, {transformations_text.lower()}. Final code: '{final_code}'"
                else:
                    # No code information - use default format
                    if len(formatted_transformations) == 1:
                        transformation_text = self._format_template(
                            "transformation_applied",
                            transformation=transformations_text.lower()
                        )
                    else:
                        transformation_text = f"After base scansion, the following adjustments were made: {transformations_text}"
                
                # Add to parts for string format
                if transformation_text:
                    self.parts.append(transformation_text)
                
                # Store in structured format
                self.structured["transformations"] = formatted_transformations
                if base_code:
                    self.structured["base_code"] = base_code
                if final_code:
                    self.structured["final_code"] = final_code
            else:
                # No valid transformations found (shouldn't happen, but handle gracefully)
                self.structured["transformations"] = []
        else:
            # No transformations available - set to empty list in structured format
            self.structured["transformations"] = []
    
    def get_explanation(
        self,
        word: Words,
        format: str = "string",
        include_technical: bool = False
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate explanation for a Words object.
        
        Args:
            word: The Words object to explain
            format: Output format - "string" or "structured" (default: "string")
            include_technical: Whether to include technical details (default: False)
        
        Returns:
            String explanation if format="string", dictionary if format="structured"
        
        Raises:
            ValueError: If format is not "string" or "structured"
        """
        # Initialize instance variables
        self.word = word
        self.parts = []
        self.structured = {}
        
        # Call component builder methods in order
        self.add_summary()
        self.add_method()
        self.add_taqti()
        self.add_steps()
        self.add_code()
        self.add_transformations()
        
        # Handle missing information edge case (Phase 4.4)
        # If no explanation parts were generated at all, add fallback message
        if not self.parts:
            word_text = self.word.word if self.word and self.word.word else "word"
            fallback = self._format_template("missing_information", word=word_text)
            if fallback:
                self.parts.append(fallback)
                self.structured["summary"] = fallback
        
        # Return result from build()
        return self.build(format)
    
    def build(self, format: str) -> Union[str, Dict[str, Any]]:
        """
        Build final explanation in requested format.
        
        Args:
            format: Output format - "string" or "structured"
        
        Returns:
            String explanation if format="string", dictionary if format="structured"
        
        Raises:
            ValueError: If format is not "string" or "structured"
        """
        if format == "string":
            # Join parts with spaces and return string
            return " ".join(self.parts) if self.parts else ""
        elif format == "structured":
            # Set full_text from joined parts
            self.structured["full_text"] = " ".join(self.parts) if self.parts else ""
            return self.structured
        else:
            raise ValueError(f"Invalid format: {format}. Must be 'string' or 'structured'")
