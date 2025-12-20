"""
Scansion with database integration via resolver pattern.

This module provides ScansionWithDatabase class that wraps Scansion and uses
WordCodeResolver to coordinate database and heuristic strategies for word code resolution.
"""

from typing import List, Optional
from aruuz.models import Words, Lines, scanOutput
from aruuz.scansion import Scansion
from aruuz.resolver import WordCodeResolver
from aruuz.database.word_lookup import WordLookup


class ScansionWithDatabase:
    """
    Scansion with database lookup via resolver pattern.
    
    This class wraps Scansion and uses WordCodeResolver to coordinate
    database and heuristic strategies for word code resolution.
    
    All methods except word_code() are delegated to the internal Scansion instance,
    ensuring the heuristics engine remains unchanged.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize with optional database path.
        
        Args:
            db_path: Optional path to SQLite database. If not provided,
                    uses default path from config. If database is unavailable,
                    gracefully falls back to heuristics-only mode.
        """
        # Internal heuristics engine (unchanged)
        self._scansion = Scansion()
        
        # Initialize resolver with database lookup (if available)
        try:
            word_lookup = WordLookup(db_path) if db_path else WordLookup()
            self._resolver = WordCodeResolver(db_lookup=word_lookup)
        except Exception:
            # Gracefully fall back to heuristics-only if DB unavailable
            self._resolver = WordCodeResolver(db_lookup=None)
    
    def add_line(self, line: Lines) -> None:
        """
        Add a line to the scansion engine.
        
        Delegated to internal Scansion instance.
        
        Args:
            line: Lines object containing the poetry line
        """
        return self._scansion.add_line(line)
    
    def scan_line(self, line: Lines, line_index: int) -> List[scanOutput]:
        """
        Process a single line and return possible scan outputs.
        
        This method overrides the base implementation to ensure word_code()
        uses the resolver (database + heuristics) instead of heuristics only.
        
        Args:
            line: Lines object to scan
            line_index: Index of the line (for reference)
            
        Returns:
            List of scanOutput objects representing possible meter matches
        """
        # Import here to avoid circular dependency
        from aruuz.meters import (
            METERS, METERS_VARIED, RUBAI_METERS,
            METER_NAMES, METERS_VARIED_NAMES, RUBAI_METER_NAMES,
            NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS,
            afail, afail_list, meter_index
        )
        from aruuz.scansion import check_code_length
        
        results: List[scanOutput] = []
        
        # Step 1: Assign codes to all words using resolver
        word_codes: List[str] = []
        for word in line.words_list:
            word = self.word_code(word)  # Use resolver-based word_code
            if len(word.code) > 0:
                word_codes.append(word.code[0])
            else:
                # If no code assigned, skip this word or use default
                word_codes.append("-")
        
        # Step 2: Build complete code string
        full_code = "".join(word_codes)
        
        if not full_code:
            return results  # No code, no matches
        
        # Step 3: Get all possible meter indices
        # Start with all regular meters
        all_meter_indices = list(range(NUM_METERS))
        
        # Add varied meters if any
        if NUM_VARIED_METERS > 0:
            all_meter_indices.extend(range(NUM_METERS, NUM_METERS + NUM_VARIED_METERS))
        
        # Add rubai meters
        if NUM_RUBAI_METERS > 0:
            all_meter_indices.extend(range(
                NUM_METERS + NUM_VARIED_METERS,
                NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
            ))
        
        # Step 4: Filter meters by code length
        matching_meters = check_code_length(full_code, all_meter_indices)
        
        # Step 5: For each matching meter, verify pattern match and create scanOutput
        for meter_idx in matching_meters:
            # Get meter pattern
            if meter_idx < NUM_METERS:
                meter_pattern = METERS[meter_idx]
                meter_name = METER_NAMES[meter_idx]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
                meter_name = METERS_VARIED_NAMES[meter_idx - NUM_METERS]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
                meter_name = RUBAI_METER_NAMES[meter_idx - NUM_METERS - NUM_VARIED_METERS] + " (رباعی)"
            else:
                continue  # Skip invalid indices
            
            # Verify pattern match: check if full code matches meter pattern
            # Create meter variations and check if code matches any
            meter_clean = meter_pattern.replace("/", "")
            meter1 = meter_clean.replace("+", "")
            meter2 = meter_clean.replace("+", "") + "-"
            meter3 = meter_clean.replace("+", "-") + "-"
            meter4 = meter_clean.replace("+", "-")
            
            matches = False
            
            # Check against all 4 variations
            for meter_var in [meter1, meter2, meter3, meter4]:
                if len(meter_var) == len(full_code):
                    match = True
                    for j in range(len(meter_var)):
                        met_char = meter_var[j]
                        code_char = full_code[j]
                        if met_char == '-':
                            if code_char != '-' and code_char != 'x':
                                match = False
                                break
                        elif met_char == '=':
                            if code_char != '=' and code_char != 'x':
                                match = False
                                break
                    if match:
                        matches = True
                        break
            
            if matches:
                # Create scanOutput
                so = scanOutput()
                so.original_line = line.original_line
                so.words = line.words_list.copy()
                so.word_taqti = word_codes.copy()
                so.word_muarrab = [w.word for w in line.words_list]  # Use original word as muarrab for now
                so.meter_name = meter_name
                so.feet = afail(meter_pattern)  # Get feet breakdown as string
                so.feet_list = afail_list(meter_pattern)  # Get feet breakdown as list with codes
                so.id = meter_idx
                so.num_lines = 1
                
                results.append(so)
        
        return results
    
    def scan_lines(self) -> List[scanOutput]:
        """
        Main method to process all lines and return scan outputs.
        
        This method overrides the base implementation to ensure it uses
        our resolver-based scan_line() method.
        
        Returns:
            List of scanOutput objects, one per line per matching meter
        """
        all_results: List[scanOutput] = []
        
        if self._scansion.free_verse or self._scansion.fuzzy:
            # For Phase 1, we don't handle free verse or fuzzy matching
            return all_results
        
        # Process each line using our resolver-based scan_line
        for k in range(self._scansion.num_lines):
            line = self._scansion.lst_lines[k]
            line_results = self.scan_line(line, k)
            all_results.extend(line_results)
        
        return all_results
    
    def word_code(self, word: Words) -> Words:
        """
        Assign scansion code to a word using resolver.
        
        This method uses WordCodeResolver to coordinate multiple strategies:
        1. Database lookup (if available)
        2. Heuristics (fallback)
        
        This is the only method that differs from the base Scansion class.
        
        Args:
            word: Words object to assign code to
            
        Returns:
            Words object with code assigned
        """
        return self._resolver.resolve(word)
    
    # Expose internal Scansion properties for compatibility
    @property
    def lst_lines(self) -> List[Lines]:
        """Access to internal lines list."""
        return self._scansion.lst_lines
    
    @property
    def num_lines(self) -> int:
        """Access to number of lines."""
        return self._scansion.num_lines
    
    @property
    def is_checked(self) -> bool:
        """Access to checked flag."""
        return self._scansion.is_checked
    
    @is_checked.setter
    def is_checked(self, value: bool) -> None:
        """Set checked flag."""
        self._scansion.is_checked = value
    
    @property
    def free_verse(self) -> bool:
        """Access to free verse flag."""
        return self._scansion.free_verse
    
    @free_verse.setter
    def free_verse(self, value: bool) -> None:
        """Set free verse flag."""
        self._scansion.free_verse = value
    
    @property
    def fuzzy(self) -> bool:
        """Access to fuzzy flag."""
        return self._scansion.fuzzy
    
    @fuzzy.setter
    def fuzzy(self, value: bool) -> None:
        """Set fuzzy flag."""
        self._scansion.fuzzy = value
    
    @property
    def error_param(self) -> int:
        """Access to error parameter."""
        return self._scansion.error_param
    
    @error_param.setter
    def error_param(self, value: int) -> None:
        """Set error parameter."""
        self._scansion.error_param = value
    
    @property
    def meter(self) -> Optional[List[int]]:
        """Access to meter."""
        return self._scansion.meter
    
    @meter.setter
    def meter(self, value: Optional[List[int]]) -> None:
        """Set meter."""
        self._scansion.meter = value

