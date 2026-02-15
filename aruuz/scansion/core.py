"""
Core Scansion class - Main orchestrator for Urdu poetry scansion.

This module contains the Scansion class that coordinates word code assignment,
meter matching, and scoring services.
"""

import logging
from typing import List, Optional, Tuple, Dict, Any, TYPE_CHECKING
from aruuz.models import Words, Lines, LineScansionResult, LineScansionResultFuzzy

if TYPE_CHECKING:
    from aruuz.models import scanPath
from aruuz.database.word_lookup import WordLookup
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS, SPECIAL_METERS,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, NUM_SPECIAL_METERS
)
from aruuz.utils.meter_summaries import METER_SUMMARIES
from .word_scansion_assigner import WordScansionAssigner
from .meter_matching import MeterMatcher
from .scoring import MeterResolver
from .explanation_builder import ExplanationBuilder

logger = logging.getLogger(__name__)


class Scansion:
    """
    Main scansion orchestrator class.
    
    Coordinates word code assignment, meter matching, and scoring services.
    """
    
    def __init__(self, word_lookup: Optional[WordLookup] = None):
        """
        Initialize Scansion instance.
        
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
        
        # Initialize word_lookup for database access (matching original behavior)
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
        
        # Initialize composed services
        self.code_assigner = WordScansionAssigner(self.word_lookup)
        self.meter_matcher = MeterMatcher(
            code_assigner=self.code_assigner,
            error_param=self.error_param,
            fuzzy=self.fuzzy,
            free_verse=self.free_verse
        )
    
    def add_line(self, line: Lines) -> None:
        """
        Add a line to be scanned.
        
        Args:
            line: Lines instance to add
        """
        self.lst_lines.append(line)
        self.num_lines += 1
    
    def assign_scansion_to_word(self, word: Words) -> Words:
        """
        Assign scansion code to a word.
        
        Args:
            word: Words instance to assign code to
            
        Returns:
            Words instance with assigned code
        """
        return self.code_assigner.assign_code_to_word(word)
    
    def match_line_to_meters(self, line: Lines, line_index: int) -> List[LineScansionResult]:
        """
        Process a single line and return possible scan outputs using tree-based matching.
        
        This is a convenience method that delegates to MeterMatcher for backward compatibility.
        
        Args:
            line: Lines instance to process
            line_index: Index of the line (0-based)
            
        Returns:
            List of LineScansionResult objects for matching meters
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        self.meter_matcher.fuzzy = self.fuzzy
        self.meter_matcher.free_verse = self.free_verse
        return self.meter_matcher.match_line_to_meters(line, line_index)
    
    def resolve_dominant_meter(self, results: List[LineScansionResult]) -> List[LineScansionResult]:
        """
        Consolidate multiple meter matches and return only those matching dominant meter.
        
        This is a convenience method that delegates to MeterResolver for backward compatibility.
        
        Args:
            results: List of LineScansionResult objects to consolidate
            
        Returns:
            List of LineScansionResult objects matching the dominant meter
        """
        return MeterResolver.resolve_dominant_meter(results)
    
    def scan_line_fuzzy(self, line: Lines, line_index: int) -> List[LineScansionResultFuzzy]:
        """
        Process a single line with fuzzy matching and return fuzzy scan outputs.
        
        This is a convenience method that delegates to MeterMatcher for backward compatibility.
        
        Args:
            line: Lines instance to process
            line_index: Index of the line (0-based)
            
        Returns:
            List of LineScansionResultFuzzy objects for matching meters
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        self.meter_matcher.fuzzy = self.fuzzy
        self.meter_matcher.free_verse = self.free_verse
        return self.meter_matcher.scan_line_fuzzy(line, line_index)
    
    def scan_lines_fuzzy(self, lines: Optional[List[Lines]] = None) -> List[LineScansionResultFuzzy]:
        """
        Process all lines with fuzzy matching and return consolidated fuzzy scan outputs.
        
        This is a convenience method that delegates to MeterMatcher for backward compatibility.
        If no lines are provided, uses self.lst_lines.
        
        Args:
            lines: Optional list of Lines instances to scan. If None, uses self.lst_lines.
            
        Returns:
            List of LineScansionResultFuzzy objects for all lines, consolidated by best meter
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        self.meter_matcher.fuzzy = self.fuzzy
        self.meter_matcher.free_verse = self.free_verse
        
        # Use self.lst_lines if no lines provided (backward compatibility)
        if lines is None:
            lines = self.lst_lines
        
        return self.meter_matcher.scan_lines_fuzzy(lines)
    
    def resolve_dominant_meter_fuzzy(self, results: List[LineScansionResultFuzzy]) -> List[LineScansionResultFuzzy]:
        """
        Consolidate fuzzy matching results and return only those matching the best meter.
        
        This is a convenience method that delegates to MeterResolver for backward compatibility.
        
        Args:
            results: List of LineScansionResultFuzzy objects to consolidate
            
        Returns:
            List of LineScansionResultFuzzy objects matching the best meter
        """
        return MeterResolver.resolve_dominant_meter_fuzzy(results)
    
    def _calculate_fuzzy_score(self, code: str, meter_pattern: str) -> Tuple[int, str]:
        """
        Calculate fuzzy score using Levenshtein distance.
        
        This is a convenience method that delegates to MeterMatcher for backward compatibility.
        
        Args:
            code: Scansion code string (e.g., "=-=")
            meter_pattern: Meter pattern string (e.g., "-===/-===/-===/-===")
            
        Returns:
            Tuple of (minimum_distance, best_matching_meter_variation)
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        return self.meter_matcher._calculate_fuzzy_score(code, meter_pattern)
    
    def match_meters_via_tree(self, line: Lines, meters: Optional[List[int]] = None) -> List['scanPath']:
        """
        Match line to meters using tree-based matching.
        
        This is a backward compatibility alias for match_meters().
        Delegates to MeterMatcher.match_meters().
        
        Args:
            line: Lines object containing words with assigned codes
            meters: Optional list of meter indices to check. If None, checks all meters.
            
        Returns:
            List of scanPath objects representing matching paths through the tree
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        self.meter_matcher.fuzzy = self.fuzzy
        self.meter_matcher.free_verse = self.free_verse
        return self.meter_matcher.match_meters(line, meters)
    
    def scan_lines(self) -> List[LineScansionResult]:
        """
        Scan all added lines and return results.
        
        This method processes all lines added to the scansion engine,
        assigns codes using heuristics, matches against meters, and
        returns all possible scan outputs.
        
        Returns:
            List of LineScansionResult objects, one per line per matching meter
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        self.meter_matcher.fuzzy = self.fuzzy
        self.meter_matcher.free_verse = self.free_verse
        
        all_results: List[LineScansionResult] = []
        
        if self.free_verse:
            # For free verse, return empty results
            return all_results
        
        if self.fuzzy:
            # Use fuzzy matching path
            fuzzy_results = self.meter_matcher.scan_lines_fuzzy(self.lst_lines)
            # Convert LineScansionResultFuzzy to LineScansionResult for compatibility
            # Note: This loses fuzzy score information but maintains API compatibility
            all_results = []
            for fr in fuzzy_results:
                so = LineScansionResult()
                so.original_line = fr.original_line
                so.words = fr.words
                so.word_taqti = fr.word_taqti
                so.meter_name = fr.meter_name
                so.meter_roman = fr.meter_roman
                so.feet = fr.feet
                so.id = fr.id
                so.is_dominant = True  # Fuzzy results are already filtered by resolve_dominant_meter_fuzzy
                all_results.append(so)
            return all_results
        
        # Process each line
        for k in range(self.num_lines):
            line = self.lst_lines[k]
            line_results = self.meter_matcher.match_line_to_meters(line, k)
            all_results.extend(line_results)
        
        # Consolidate results: resolve_dominant_meter() returns only results matching dominant meter
        if all_results:
            all_results = MeterResolver.resolve_dominant_meter(all_results)
            # Mark all returned results as dominant (they're already filtered)
            for result in all_results:
                result.is_dominant = True
        
        return all_results
    
    def follows_meter_foot_order(self, line_arkaan: List[str], feet: List[str]) -> bool:
        """
        Check if line feet are in the same order as meter feet.
        
        This is a backward compatibility method.
        
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
    
    def calculate_meter_match_score(self, meter: str, line_feet: str) -> int:
        """
        Calculate score for how well a line matches a meter.
        
        This is a backward compatibility wrapper that delegates to MeterResolver.calculate_score().
        
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
        return MeterResolver.calculate_score(meter, line_feet)
    
    def ordered_match_count(self, line_feet: List[str], meter_feet: List[str]) -> int:
        """
        Count how many feet from line_feet appear in meter_feet in correct relative order.
        
        This is a backward compatibility wrapper that delegates to MeterResolver.ordered_match_count().
        
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
        return MeterResolver.ordered_match_count(line_feet, meter_feet)
    
    def _get_meter_pattern(self, so: LineScansionResult, feet_list_dict: List[Dict[str, str]]) -> Optional[str]:
        """
        Extract meter pattern code from a LineScansionResult.
        
        This helper method determines the meter pattern by:
        1. Checking if the result has a valid meter ID and extracting from METERS arrays
        2. Falling back to concatenating foot codes if no valid meter ID
        
        Args:
            so: LineScansionResult object containing meter information
            feet_list_dict: List of dictionaries with 'foot' and 'code' keys
            
        Returns:
            Meter pattern string (e.g., "-===-===") or None if unavailable
        """
        if so.meter_name != 'No meter match found' and so.id is not None:
            try:
                if 0 <= so.id < NUM_METERS:
                    return METERS[so.id].replace("/", "")
                elif so.id < NUM_METERS + NUM_VARIED_METERS:
                    return METERS_VARIED[so.id - NUM_METERS].replace("/", "")
                elif so.id < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                    return RUBAI_METERS[so.id - NUM_METERS - NUM_VARIED_METERS].replace("/", "")
                elif so.id <= -2 and feet_list_dict:
                    return ''.join(foot['code'] for foot in feet_list_dict)
            except (IndexError, TypeError):
                pass
        return ''.join(foot['code'] for foot in feet_list_dict) if feet_list_dict else None
    
    def _build_word_codes(self, so: LineScansionResult) -> List[Dict[str, Any]]:
        """
        Build word codes list from a LineScansionResult, including explanations.
        
        Args:
            so: LineScansionResult object containing words and word_taqti
            
        Returns:
            List of dictionaries with 'word', 'code', and 'explanation' keys.
            Each explanation is generated using ExplanationBuilder.
        """
        explanation_builder = ExplanationBuilder()
        word_codes = []
        
        for i, word in enumerate(so.words):
            word_code = {
                'word': word.word,
                'code': so.word_taqti[i] if i < len(so.word_taqti) else ""
            }
            
            # Generate explanation for this word
            try:
                explanation = explanation_builder.get_explanation(word, format="string")
                word_code['explanation'] = explanation if explanation else ""
            except Exception as e:
                # If explanation generation fails, log and continue without explanation
                logger.warning(f"Failed to generate explanation for word '{word.word}': {e}")
                word_code['explanation'] = ""
            
            word_codes.append(word_code)
        
        return word_codes
    
    def _build_feet_list_dict(self, so: LineScansionResult) -> List[Dict[str, str]]:
        """
        Build feet list dictionary from a LineScansionResult.
        
        Args:
            so: LineScansionResult object containing feet_list
            
        Returns:
            List of dictionaries with 'foot' and 'code' keys
        """
        return [{'foot': foot_obj.foot, 'code': foot_obj.code} for foot_obj in so.feet_list]
    
    def get_scansion(self) -> Dict[str, Any]:
        """
        Comprehensive scansion method that returns everything needed for display.
        
        This is a "kitchen sink" method that processes all added lines, performs
        meter matching, resolves dominant meters, and returns a complete data
        structure ready for use in web templates or API responses.
        
        The method:
        1. Gets all meter matches per line (without per-line dominant resolution)
        2. Determines overall dominant bahrs across the entire poem
        3. Builds a comprehensive result structure with:
           - Per-line results with all meter candidates
           - Word codes with explanations, feet breakdowns, and meter patterns
           - Default selection based on dominant bahrs
           - Fallback handling for lines with no matches
        
        Returns:
            Dictionary containing:
            - 'line_results': List of line result dictionaries, each containing:
              - 'line_index': 0-based index of the line
              - 'original_line': Original line text
              - 'results': List of meter match results, each containing:
                - 'meter_name': Name of the meter (or "No meter match found")
                - 'meter_roman': Roman transliteration of the meter name (with diacritics), or empty if not available
                - 'feet': Feet breakdown as string
                - 'feet_list': List of dicts with 'foot' and 'code' keys
                - 'word_codes': List of dicts with 'word', 'code', and 'explanation' keys.
                  Each explanation is a user-friendly string explaining why the word
                  was scanned with that particular code (generated using ExplanationBuilder)
                - 'full_code': Concatenated scansion code string
                - 'meter_pattern': Meter pattern code extracted from meter ID or feet
                - 'is_default': Boolean indicating if this matches dominant bahr
                - 'meter_id': Internal meter ID (for reference)
            - 'poem_dominant_bahrs': List of dominant meter names across all lines
            - 'poem_dominant_bahrs_info': List of dicts with 'name', 'roman', 'summary' (from meter_summaries)
            - 'num_lines': Total number of lines processed
            - 'fuzzy_mode': Boolean indicating if fuzzy matching was used
            - 'free_verse_mode': Boolean indicating if free verse mode was enabled
            - 'error_param': Error parameter used for matching
        
        Example:
            >>> scanner = Scansion()
            >>> scanner.add_line(Lines("کوئی امید بر نہیں آتی"))
            >>> result = scanner.get_scansion()
            >>> print(result['poem_dominant_bahrs'])
            ['رمل مثمن محذوف']
            >>> print(result['line_results'][0]['results'][0]['meter_name'])
            'رمل مثمن محذوف'
        """
        # Update MeterMatcher properties in case they changed after initialization
        self.meter_matcher.error_param = self.error_param
        self.meter_matcher.fuzzy = self.fuzzy
        self.meter_matcher.free_verse = self.free_verse
        
        # Initialize return structure
        line_results: List[Dict[str, Any]] = []
        poem_dominant_bahrs: List[str] = []
        
        # Handle empty lines case
        if self.num_lines == 0:
            return {
                'line_results': [],
                'poem_dominant_bahrs': [],
                'poem_dominant_bahrs_roman': [],
                'poem_dominant_bahrs_info': [],
                'num_lines': 0,
                'fuzzy_mode': self.fuzzy,
                'free_verse_mode': self.free_verse,
                'error_param': self.error_param
            }
        
        # Step 1: Get all meter matches per line (no per-line resolve_dominant_meter)
        # This preserves all candidates for each line before overall dominant resolution
        per_line_candidates: List[List[LineScansionResult]] = []
        for idx in range(self.num_lines):
            line = self.lst_lines[idx]
            candidates = self.match_line_to_meters(line, idx)
            per_line_candidates.append(candidates if candidates else [])
        
        # Step 2: Get overall dominant bahr for entire poem (scan_lines across all lines)
        # This uses resolve_dominant_meter internally to find the most common meter
        poem_scan_results = self.scan_lines()
        poem_dominant_bahrs = list({
            so.meter_name for so in poem_scan_results
            if so.is_dominant and so.meter_name and so.meter_name != 'No meter match found'
        })
        # Roman and summary from meter_summaries (same order as poem_dominant_bahrs)
        name_to_roman: Dict[str, str] = {}
        for so in poem_scan_results:
            if so.meter_name and so.meter_name not in name_to_roman:
                name_to_roman[so.meter_name] = getattr(so, 'meter_roman', '') or ''
        poem_dominant_bahrs_info: List[Dict[str, Any]] = []
        for n in poem_dominant_bahrs:
            info = METER_SUMMARIES.get(n)
            if info:
                poem_dominant_bahrs_info.append({
                    'name': n,
                    'roman': info['roman'],
                    'bahr_short': info.get('bahr_short', ''),
                    'bahr_meaning': info.get('bahr_meaning', ''),
                    'summary': info['summary'],
                })
            else:
                r = name_to_roman.get(n, '')
                poem_dominant_bahrs_info.append({
                    'name': n,
                    'roman': r,
                    'bahr_short': r.split()[0] if r else '',
                    'bahr_meaning': '',
                    'summary': '',
                })
        poem_dominant_bahrs_roman = [i['roman'] for i in poem_dominant_bahrs_info]
        
        # Step 3: Build comprehensive line_results structure for template/API
        for idx in range(self.num_lines):
            line_obj = self.lst_lines[idx]
            candidates = per_line_candidates[idx]
            
            line_result: Dict[str, Any] = {
                'line_index': idx,
                'original_line': line_obj.original_line,
                'results': []
            }
            
            if candidates:
                # Deduplicate by meter_name: keep first occurrence of each
                # This ensures one result per unique meter name per line
                seen_meter_names = set()
                unique_candidates: List[LineScansionResult] = []
                for so in candidates:
                    if so.meter_name not in seen_meter_names:
                        seen_meter_names.add(so.meter_name)
                        unique_candidates.append(so)
                
                # Determine default result: prefer one matching dominant bahr, else first candidate
                default_so = next(
                    (so for so in unique_candidates if so.meter_name in poem_dominant_bahrs),
                    unique_candidates[0] if unique_candidates else None
                )
                
                # Build result dictionaries for each unique meter candidate
                for so in unique_candidates:
                    feet_list_dict = self._build_feet_list_dict(so)
                    meter_pattern = self._get_meter_pattern(so, feet_list_dict)
                    
                    line_result['results'].append({
                        'meter_name': so.meter_name,
                        'meter_roman': so.meter_roman,
                        'feet': so.feet,
                        'feet_list': feet_list_dict,
                        'word_codes': self._build_word_codes(so),
                        'full_code': ''.join(so.word_taqti),
                        'original_line': so.original_line,
                        'meter_pattern': meter_pattern,
                        'is_default': (so is default_so),
                        'meter_id': so.id,
                    })
            else:
                # No meter match found: still provide word codes for display
                # This ensures the UI can show scansion codes even without meter matches
                explanation_builder = ExplanationBuilder()
                word_codes = []
                
                for word in line_obj.words_list:
                    # Assign scansion code to word
                    w = self.assign_scansion_to_word(word)
                    
                    word_code = {
                        'word': w.word,
                        'code': w.code[0] if w.code else "-"
                    }
                    
                    # Generate explanation for this word
                    try:
                        explanation = explanation_builder.get_explanation(w, format="string")
                        word_code['explanation'] = explanation if explanation else ""
                    except Exception as e:
                        # If explanation generation fails, log and continue without explanation
                        logger.warning(f"Failed to generate explanation for word '{w.word}': {e}")
                        word_code['explanation'] = ""
                    
                    word_codes.append(word_code)
                
                line_result['results'].append({
                    'meter_name': 'No meter match found',
                    'meter_roman': '',
                    'feet': '',
                    'word_codes': word_codes,
                    'full_code': ''.join(wc['code'] for wc in word_codes),
                    'original_line': line_obj.original_line,
                    'feet_list': [],
                    'meter_pattern': None,
                    'is_default': True,
                    'meter_id': None,
                })
            
            line_results.append(line_result)
        
        # Return comprehensive result structure
        return {
            'line_results': line_results,
            'poem_dominant_bahrs': poem_dominant_bahrs,
            'poem_dominant_bahrs_roman': poem_dominant_bahrs_roman,
            'poem_dominant_bahrs_info': poem_dominant_bahrs_info,
            'num_lines': self.num_lines,
            'fuzzy_mode': self.fuzzy,
            'free_verse_mode': self.free_verse,
            'error_param': self.error_param
        }