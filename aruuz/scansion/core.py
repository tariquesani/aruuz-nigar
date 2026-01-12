"""
Core Scansion class - Main orchestrator for Urdu poetry scansion.

This module contains the Scansion class that coordinates word code assignment,
meter matching, and scoring services.
"""

import logging
from typing import List, Optional, Tuple, TYPE_CHECKING
from aruuz.models import Words, Lines, LineScansionResult, LineScansionResultFuzzy

if TYPE_CHECKING:
    from aruuz.models import scanPath
from aruuz.database.word_lookup import WordLookup
from .word_scansion_assigner import WordScansionAssigner
from .meter_matching import MeterMatcher
from .scoring import MeterResolver

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
            word_lookup: Optional WordLookup instance for database access
        """
        self.lst_lines: List[Lines] = []
        self.num_lines: int = 0
        self.is_checked: bool = False
        self.free_verse: bool = False
        self.fuzzy: bool = False
        self.error_param: int = 8
        self.meter: Optional[List[int]] = None
        
        # Initialize composed services
        self.code_assigner = WordScansionAssigner(word_lookup)
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
