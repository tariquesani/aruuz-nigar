"""
Meter Matching Service

Service class for matching lines to meters using tree-based matching.
"""

from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from aruuz.models import Lines, LineScansionResult, LineScansionResultFuzzy, scanPath, codeLocation

from .prosodic_rules import ProsodicRules
from .word_scansion_assigner import WordScansionAssigner
from .scoring import MeterResolver
from aruuz.tree.code_tree import CodeTree
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS, SPECIAL_METERS,
    METER_NAMES, METERS_VARIED_NAMES, RUBAI_METER_NAMES, SPECIAL_METER_NAMES,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, NUM_SPECIAL_METERS,
    afail, afail_list, meter_index, afail_hindi, zamzama_feet, hindi_feet
)


class MeterMatcher:
    """
    Service class for meter matching.
    
    Handles tree-based meter matching, fuzzy matching, and free verse processing.
    """
    
    def __init__(
        self,
        code_assigner: WordScansionAssigner,
        error_param: int = 8,
        fuzzy: bool = False,
        free_verse: bool = False
    ):
        """
        Initialize MeterMatcher.
        
        Args:
            code_assigner: WordScansionAssigner instance for assigning codes to words
            error_param: Error tolerance parameter (default: 8)
            fuzzy: Enable fuzzy matching (default: False)
            free_verse: Enable free verse mode (default: False)
        """
        self.code_assigner = code_assigner
        self.error_param = error_param
        self.fuzzy = fuzzy
        self.free_verse = free_verse
    
    def match_meters(self, line: 'Lines', meters: Optional[List[int]] = None) -> List['scanPath']:
        """
        Match line to meters using tree-based matching.
        
        Renamed from match_meters_via_tree().
        
        This method builds a tree structure from the word codes in the line and
        uses tree-based traversal to efficiently match against meter patterns.
        This is the main entry point for tree-based pattern matching.
        
        Args:
            line: Lines object containing words with assigned codes
            meters: Optional list of meter indices to check. If None, checks all meters.
        
        Returns:
            List of scanPath objects representing matching paths through the tree
        """
        # Build CodeTree from line
        # The build_from_line method handles both regular codes and taqti_word_graft codes
        tree = CodeTree.build_from_line(
            line,
            error_param=self.error_param,
            fuzzy=self.fuzzy,
            free_verse=self.free_verse
        )
        
        # Call tree.find_meter() to get scanPath results
        return tree.find_meter(meters)
    
    def match_line_to_meters(self, line: 'Lines', line_index: int) -> List['LineScansionResult']:
        """
        Process a single line and return possible scan outputs using tree-based matching.
        
        This method:
        1. Assigns codes to all words in the line
        2. Applies prosodic rules (Al, Izafat, Ataf, Word Grafting)
        3. Uses tree-based find_meter() to find matching meters
        4. Converts scanPath results to LineScansionResult objects
        
        Args:
            line: Lines object to scan
            line_index: Index of the line (for reference)
            
        Returns:
            List of LineScansionResult objects representing possible meter matches
        """
        from aruuz.models import LineScansionResult, Words
        
        results: List[LineScansionResult] = []
        
        # Step 1: Assign codes to all words (needed for tree building)
        for word in line.words_list:
            self.code_assigner.assign_code_to_word(word)
        
        # Step 1.5-1.8: Apply prosodic rules (Al → Izafat → Ataf → Word Grafting)
        ProsodicRules.process_al_prefix(line)
        ProsodicRules.process_izafat(line)
        ProsodicRules.process_ataf(line)
        ProsodicRules.process_word_grafting(line)
        
        # Step 2: Use tree-based match_meters() to get matching scanPaths
        # match_meters() handles tree building, pattern matching, and meter filtering
        scan_paths = self.match_meters(line)
        
        if not scan_paths:
            return results  # No matches found
        
        # Step 3: Convert scanPath results to LineScansionResult objects
        for sp in scan_paths:
            if not sp.meters:
                continue  # Skip paths with no matching meters
            
            # Extract words and codes from scanPath location (skip index 0 which is root)
            words_list: List[Words] = []
            word_taqti_list: List[str] = []
            
            for i in range(1, len(sp.location)):
                loc = sp.location[i]
                if loc.word_ref >= 0 and loc.word_ref < len(line.words_list):
                    words_list.append(line.words_list[loc.word_ref])
                    word_taqti_list.append(loc.code)
            
            # Build full code string from word codes
            full_code = "".join(word_taqti_list)
            
            if not full_code:
                continue  # Skip if no code
            
            # Step 4: Create LineScansionResult for each matching meter
            for meter_idx in sp.meters:
                so = LineScansionResult()
                so.original_line = line.original_line
                so.words = words_list.copy()
                so.word_taqti = word_taqti_list.copy()
                so.word_muarrab = [w.word for w in words_list]  # Use original word as muarrab
                so.num_lines = 1
                
                # Determine meter pattern, name, and feet based on meter index
                if meter_idx < NUM_METERS:
                    # Regular meter
                    meter_pattern = METERS[meter_idx]
                    so.meter_name = METER_NAMES[meter_idx]
                    so.feet = afail(meter_pattern)
                    so.feet_list = afail_list(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                    # Varied meter
                    meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
                    so.meter_name = METERS_VARIED_NAMES[meter_idx - NUM_METERS]
                    so.feet = afail(meter_pattern)
                    so.feet_list = afail_list(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                    # Rubai meter
                    meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
                    so.meter_name = RUBAI_METER_NAMES[meter_idx - NUM_METERS - NUM_VARIED_METERS] + " (رباعی)"
                    so.feet = afail(meter_pattern)
                    so.feet_list = afail_list(meter_pattern)
                    so.id = -2
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS + NUM_SPECIAL_METERS:
                    # Special meter (Hindi/Zamzama)
                    special_idx = meter_idx - NUM_METERS - NUM_VARIED_METERS - NUM_RUBAI_METERS
                    if special_idx < len(SPECIAL_METER_NAMES):
                        so.meter_name = SPECIAL_METER_NAMES[special_idx]
                        # Get scansion code from scanPath and generate feet dynamically
                        if special_idx > 7:
                            # Zamzama meters (indices 8-10)
                            so.feet, so.feet_list = zamzama_feet(special_idx, full_code)
                        else:
                            # Hindi meters (indices 0-7)
                            so.feet, so.feet_list = hindi_feet(special_idx, full_code)
                        # Fall back to static afail_hindi if dynamic generation failed
                        if not so.feet:
                            so.feet = afail_hindi(so.meter_name)
                            so.feet_list = []
                        so.id = -2 - special_idx
                    else:
                        continue  # Skip invalid special meter index
                else:
                    continue  # Skip invalid meter index
                
                results.append(so)
        
        return results
    
    def _calculate_fuzzy_score(self, code: str, meter_pattern: str) -> Tuple[int, str]:
        """
        Calculate fuzzy score using Levenshtein distance.
        
        Creates 4 meter variations and calculates Levenshtein distance for each,
        returning the minimum distance and the best matching meter variation.
        
        The 4 variations are:
        1. Original meter with '+' removed
        2. Meter with '+' removed + "~" appended
        3. Meter with '+' replaced by "~" + "~" appended
        4. Meter with '+' replaced by "~"
        
        Args:
            code: Scansion code string (e.g., "=-=")
            meter_pattern: Meter pattern string (e.g., "-===/-===/-===/-===")
            
        Returns:
            Tuple of (minimum_distance, best_matching_meter_variation) where:
            - minimum_distance: Minimum Levenshtein distance across all 4 meter variations
            - best_matching_meter_variation: The meter variation with the minimum distance
        """
        from aruuz.models import codeLocation
        
        # Remove '/' from meter
        meter = meter_pattern.replace("/", "")
        
        # Create 4 variations (must create before removing '+' from meter)
        meter1 = meter.replace("+", "")
        meter2 = meter.replace("+", "") + "~"
        meter3 = meter.replace("+", "~") + "~"
        meter4 = meter.replace("+", "~")
        
        # Create a temporary CodeTree instance to access _levenshtein_distance
        # We can use any codeLocation for initialization
        temp_loc = codeLocation(code="", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        temp_tree = CodeTree(temp_loc)
        temp_tree.error_param = self.error_param
        
        # Calculate Levenshtein distance for each variation
        score1 = temp_tree._levenshtein_distance(meter1, code)
        score2 = temp_tree._levenshtein_distance(meter2, code)
        score3 = temp_tree._levenshtein_distance(meter3, code)
        score4 = temp_tree._levenshtein_distance(meter4, code)
        
        # Find minimum distance and corresponding meter variation
        scores = [(score1, meter1), (score2, meter2), (score3, meter3), (score4, meter4)]
        min_score, best_meter = min(scores, key=lambda x: x[0])
        
        return (min_score, best_meter)
    
    def scan_line_fuzzy(self, line: 'Lines', line_index: int) -> List['LineScansionResultFuzzy']:
        """
        Process a single line with fuzzy matching and return fuzzy scan outputs.
        
        This method:
        1. Assigns codes to all words in the line
        2. Applies prosodic rules (Al, Izafat, Ataf, Word Grafting)
        3. Temporarily enables fuzzy mode and uses tree-based find_meter() to find matching meters
        4. Converts scanPath results to LineScansionResultFuzzy objects
        5. Calculates fuzzy scores using Levenshtein distance
        
        Args:
            line: Lines object to scan
            line_index: Index of the line (for reference)
            
        Returns:
            List of LineScansionResultFuzzy objects representing possible meter matches with scores
        """
        from aruuz.models import LineScansionResultFuzzy, Words
        
        results: List[LineScansionResultFuzzy] = []
        
        # Step 1: Assign codes to all words (needed for tree building)
        for word in line.words_list:
            self.code_assigner.assign_code_to_word(word)
        
        # Step 1.5-1.8: Apply prosodic rules (Al → Izafat → Ataf → Word Grafting)
        ProsodicRules.process_al_prefix(line)
        ProsodicRules.process_izafat(line)
        ProsodicRules.process_ataf(line)
        ProsodicRules.process_word_grafting(line)
        
        # Step 2: Temporarily enable fuzzy mode and use tree-based find_meter()
        # Save original fuzzy state
        original_fuzzy = self.fuzzy
        self.fuzzy = True
        
        try:
            # match_meters() handles tree building with fuzzy mode enabled
            scan_paths = self.match_meters(line)
        finally:
            # Restore original fuzzy state
            self.fuzzy = original_fuzzy
        
        if not scan_paths:
            return results  # No matches found
        
        # Step 3: Convert scanPath results to LineScansionResultFuzzy objects
        for sp in scan_paths:
            if not sp.meters:
                continue  # Skip paths with no matching meters
            
            # Extract words and codes from scanPath location (skip index 0 which is root)
            words_list: List[Words] = []
            word_taqti_list: List[str] = []
            
            for i in range(1, len(sp.location)):
                loc = sp.location[i]
                if loc.word_ref >= 0 and loc.word_ref < len(line.words_list):
                    words_list.append(line.words_list[loc.word_ref])
                    word_taqti_list.append(loc.code)
            
            # Build full code string from word codes
            full_code = "".join(word_taqti_list)
            
            if not full_code:
                continue  # Skip if no code
            
            # Step 4: Create LineScansionResultFuzzy for each matching meter
            for meter_idx in sp.meters:
                so = LineScansionResultFuzzy()
                so.original_line = line.original_line
                so.words = words_list.copy()
                so.word_taqti = word_taqti_list.copy()
                so.original_taqti = word_taqti_list.copy()  # Same as word_taqti for now
                so.error = [False] * len(words_list)  # Initialize error flags
                
                # Determine meter pattern, name, and feet based on meter index
                meter_pattern = ""
                if meter_idx < NUM_METERS:
                    # Regular meter
                    meter_pattern = METERS[meter_idx]
                    so.meter_name = METER_NAMES[meter_idx]
                    so.feet = afail(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                    # Varied meter
                    meter_pattern = METERS_VARIED[meter_idx - NUM_METERS]
                    so.meter_name = METERS_VARIED_NAMES[meter_idx - NUM_METERS]
                    so.feet = afail(meter_pattern)
                    so.id = meter_idx
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                    # Rubai meter
                    meter_pattern = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS]
                    so.meter_name = RUBAI_METER_NAMES[meter_idx - NUM_METERS - NUM_VARIED_METERS] + " (رباعی)"
                    so.feet = afail(meter_pattern)
                    so.id = -2
                elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS + NUM_SPECIAL_METERS:
                    # Special meter (Hindi/Zamzama)
                    special_idx = meter_idx - NUM_METERS - NUM_VARIED_METERS - NUM_RUBAI_METERS
                    if special_idx < len(SPECIAL_METER_NAMES):
                        so.meter_name = SPECIAL_METER_NAMES[special_idx]
                        # Get scansion code from scanPath and generate feet dynamically
                        if special_idx > 7:
                            # Zamzama meters (indices 8-10)
                            so.feet, so.feet_list = zamzama_feet(special_idx, full_code)
                        else:
                            # Hindi meters (indices 0-7)
                            so.feet, so.feet_list = hindi_feet(special_idx, full_code)
                        # Fall back to static afail_hindi if dynamic generation failed
                        if not so.feet:
                            so.feet = afail_hindi(so.meter_name)
                            so.feet_list = []
                        so.id = -2 - special_idx
                        # For special meters, we don't have a standard pattern, so skip score calculation
                        so.score = 10  # Default score
                    else:
                        continue  # Skip invalid special meter index
                else:
                    continue  # Skip invalid meter index
                
                # Calculate fuzzy score using Levenshtein distance
                # Only calculate if we have a meter pattern
                if meter_pattern:
                    min_distance, best_meter = self._calculate_fuzzy_score(full_code, meter_pattern)
                    so.score = min_distance
                
                # Initialize meter_syllables and code_syllables (can be populated later if needed)
                so.meter_syllables = []
                so.code_syllables = []
                
                results.append(so)
        
        return results
    
    def scan_lines_fuzzy(self, lines: List['Lines']) -> List['LineScansionResultFuzzy']:
        """
        Process all lines with fuzzy matching and return consolidated fuzzy scan outputs.
        
        This method:
        1. Iterates through all lines in the provided list
        2. Calls scan_line_fuzzy() for each line
        3. Collects all LineScansionResultFuzzy results
        4. Calls MeterResolver.resolve_dominant_meter_fuzzy() to consolidate results
        5. Returns List[LineScansionResultFuzzy]
        
        Args:
            lines: List of Lines instances to scan
            
        Returns:
            List of LineScansionResultFuzzy objects for all lines, consolidated by best meter
        """
        all_results: List['LineScansionResultFuzzy'] = []
        
        # Process each line
        for k in range(len(lines)):
            line = lines[k]
            line_results = self.scan_line_fuzzy(line, k)
            all_results.extend(line_results)
        
        # Consolidate results: resolve_dominant_meter_fuzzy() returns only results matching best meter
        if all_results:
            all_results = MeterResolver.resolve_dominant_meter_fuzzy(all_results)
        
        return all_results
