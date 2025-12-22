"""
Code tree for pattern matching.

This module implements tree structures for matching word codes to meter patterns.
"""

from typing import List, Optional
from aruuz.models import codeLocation, Lines, Words, scanPath
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, USAGE
)


class CodeTree:
    """
    Tree structure for organizing word codes for efficient meter matching.
    
    This class builds a tree from word codes in a line of poetry, allowing
    efficient traversal and pattern matching against meter patterns.
    
    Attributes:
        location: The codeLocation at this node
        children: List of child CodeTree nodes
        error_param: Error parameter for fuzzy matching (default: 2)
        fuzzy: Flag for fuzzy matching mode (default: False)
        free_verse: Flag for free verse mode (default: False)
    """
    
    def __init__(self, loc: codeLocation):
        """
        Initialize a CodeTree node.
        
        Args:
            loc: The codeLocation for this node
        """
        self.location: codeLocation = codeLocation(
            code=loc.code,
            word_ref=loc.word_ref,
            code_ref=loc.code_ref,
            word=loc.word,
            fuzzy=loc.fuzzy
        )
        self.children: List['CodeTree'] = []
        self.error_param: int = 2
        self.fuzzy: bool = False
        self.free_verse: bool = False
    
    def add_child(self, loc: codeLocation) -> None:
        """
        Recursively add a child node to the tree.
        
        This method implements recursive tree building logic:
        - If children exist and the new location has the same wordRef as the first child,
          it checks if a child with the same codeRef already exists. If not, adds a new child.
        - If children exist but with different wordRef, recursively calls add_child on all children.
        - If no children exist and this node's wordRef is one less than the new location's wordRef
          (sequential words), adds the new child.
        
        Args:
            loc: The codeLocation to add as a child
        """
        if len(self.children) > 0:
            # Check if first child has the same wordRef as the new location
            if self.children[0].location.word_ref == loc.word_ref:
                # Same word - check if codeRef already exists
                flag = False
                for child in self.children:
                    if loc.code_ref == child.location.code_ref:
                        flag = True
                        break
                
                # If codeRef doesn't exist, add new child
                if not flag:
                    child = CodeTree(loc)
                    child.error_param = self.error_param
                    child.fuzzy = self.fuzzy
                    child.free_verse = self.free_verse
                    self.children.append(child)
            else:
                # Different word - recursively add to all children
                for child in self.children:
                    child.error_param = self.error_param
                    child.fuzzy = self.fuzzy
                    child.free_verse = self.free_verse
                    child.add_child(loc)
        else:
            # No children - add if sequential word
            if self.location.word_ref == loc.word_ref - 1:
                child = CodeTree(loc)
                child.error_param = self.error_param
                child.fuzzy = self.fuzzy
                child.free_verse = self.free_verse
                self.children.append(child)
    
    @classmethod
    def build_from_line(cls, line: Lines, error_param: int = 2, 
                       fuzzy: bool = False, free_verse: bool = False) -> 'CodeTree':
        """
        Build a CodeTree from a Lines object.
        
        This method creates a root node and then adds all word codes from the line
        to build the complete tree structure. It handles both regular codes and
        taqti_word_graft codes.
        
        Args:
            line: The Lines object containing words with codes
            error_param: Error parameter for fuzzy matching (default: 2)
            fuzzy: Flag for fuzzy matching mode (default: False)
            free_verse: Flag for free verse mode (default: False)
        
        Returns:
            A CodeTree instance with all word codes added
        """
        # Create root node
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = cls(root_loc)
        tree.error_param = error_param
        tree.fuzzy = fuzzy
        tree.free_verse = free_verse
        
        # Track codes we've already added for each word to avoid duplicates
        for w in range(len(line.words_list)):
            wrd: Words = line.words_list[w]
            code_list: List[str] = []
            
            # Add regular codes
            for i in range(len(wrd.code)):
                code = wrd.code[i]
                
                # Check if we've already added this code for this word
                if code not in code_list:
                    cd = codeLocation(
                        code=code,
                        code_ref=i,
                        word_ref=w,
                        word=wrd.word,
                        fuzzy=0
                    )
                    code_list.append(code)
                    tree.add_child(cd)
            
            # Add taqti_word_graft codes
            for k in range(len(wrd.taqti_word_graft)):
                graft_code = wrd.taqti_word_graft[k]
                
                # Check if we've already added this code for this word
                if graft_code not in code_list:
                    cd = codeLocation(
                        code=graft_code,
                        code_ref=len(wrd.code) + k,
                        word_ref=w,
                        word=wrd.word,
                        fuzzy=0
                    )
                    code_list.append(graft_code)
                    tree.add_child(cd)
        
        return tree
    
    def _is_match(self, meter: str, tentative_code: str, word_code: str) -> bool:
        """
        Check if a meter pattern matches a code sequence.
        
        This method compares a meter pattern with a tentative code (already processed)
        and a word code. It handles 4 variations of the meter pattern:
        1. Original meter with '+' removed
        2. Meter with '+' removed + '-' appended
        3. Meter with '+' replaced by '-' + '-' appended
        4. Meter with '+' replaced by '-'
        
        It also checks caesura positions (word boundaries marked by '+' in meter).
        
        Args:
            meter: Meter pattern string (e.g., "-===/-===/-===/-===")
            tentative_code: Already processed code from previous words
            word_code: Code for the current word
            
        Returns:
            True if any variation of the meter matches the code, False otherwise
        """
        if len(tentative_code) + len(word_code) == 0:
            return False
        
        # Remove '/' from meter
        meter_original = meter.replace("/", "")
        
        # Caesura detection (must check before removing '+')
        # If meter has '+' at position after tentativeCode + wordCode, 
        # wordCode must end with '-'
        if len(meter_original) > len(tentative_code) + len(word_code):
            caesura_pos = len(tentative_code) + len(word_code) - 1
            if caesura_pos >= 0 and caesura_pos < len(meter_original) and meter_original[caesura_pos] == '+':
                if len(word_code) >= 2:
                    if word_code[-1] != '-':
                        return False  # Word-boundary caesura violation
                # If word_code length == 1, it's allowed (no check needed)
        
        # Create 4 variations of the meter
        meter2 = meter_original.replace("+", "") + "-"
        meter3 = meter_original.replace("+", "-") + "-"
        meter4 = meter_original.replace("+", "-")
        meter = meter_original.replace("+", "")
        
        # Flags for each variation (True = match, False = no match)
        flag1 = True
        flag2 = True
        flag3 = True
        flag4 = True
        
        code = word_code
        
        # Variation 1: Original meter
        if not (len(meter) < len(tentative_code) + len(word_code)):
            meter_sub = meter[len(tentative_code):]
            i = 0
            while i < len(code):
                if i >= len(meter_sub):
                    flag1 = False
                    break
                met = meter_sub[i]
                cd = code[i]
                
                # Pattern matching
                if met == '-':
                    if cd == '-' or cd == 'x':
                        i += 1
                    else:
                        flag1 = False
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        i += 1
                    else:
                        flag1 = False
                        break
        else:
            flag1 = False
        
        # Variation 2: meter2 (meter with '+' removed + '-' appended)
        meter = meter2
        i = 0
        if not (len(meter) < len(tentative_code) + len(word_code)):
            meter_sub = meter[len(tentative_code):]
            while i < len(code):
                if i >= len(meter_sub):
                    flag2 = False
                    break
                met = meter_sub[i]
                cd = code[i]
                
                # Special check for last character
                if i == len(code) - 1:
                    if cd != '-':
                        flag2 = False
                        break
                
                # Pattern matching
                if met == '-':
                    if cd == '-' or cd == 'x':
                        i += 1
                    else:
                        flag2 = False
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        i += 1
                    else:
                        flag2 = False
                        break
        else:
            flag2 = False
        
        # Variation 3: meter3 (meter with '+' replaced by '-' + '-' appended)
        meter = meter3
        i = 0
        if not (len(meter) < len(tentative_code) + len(word_code)):
            meter_sub = meter[len(tentative_code):]
            while i < len(code):
                if i >= len(meter_sub):
                    flag3 = False
                    break
                met = meter_sub[i]
                cd = code[i]
                
                # Special check for last character
                if i == len(code) - 1:
                    if cd != '-':
                        flag3 = False
                        break
                
                # Pattern matching
                if met == '-':
                    if cd == '-' or cd == 'x':
                        i += 1
                    else:
                        flag3 = False
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        i += 1
                    else:
                        flag3 = False
                        break
        else:
            flag3 = False
        
        # Variation 4: meter4 (meter with '+' replaced by '-')
        meter = meter4
        i = 0
        if not (len(meter) < len(tentative_code) + len(word_code)):
            meter_sub = meter[len(tentative_code):]
            while i < len(code):
                if i >= len(meter_sub):
                    flag4 = False
                    break
                met = meter_sub[i]
                cd = code[i]
                
                # Pattern matching
                if met == '-':
                    if cd == '-' or cd == 'x':
                        i += 1
                    else:
                        flag4 = False
                        break
                elif met == '=':
                    if cd == '=' or cd == 'x':
                        i += 1
                    else:
                        flag4 = False
                        break
        else:
            flag4 = False
        
        # Return True if any variation matches
        return flag1 or flag2 or flag3 or flag4
    
    def _check_code_length(self, code: str, indices: List[int]) -> List[int]:
        """
        Filter meter indices by checking if code length matches any meter variation.
        
        This method checks if the given code length matches any of the 4 variations
        of each meter pattern. Meters that don't match any variation are removed.
        
        The 4 variations are:
        1. Original meter with '+' removed
        2. Meter with '+' removed + '-' appended
        3. Meter with '+' replaced by '-' + '-' appended
        4. Meter with '+' replaced by '-'
        
        Args:
            code: Scansion code string (e.g., "=-=")
            indices: List of meter indices to check
            
        Returns:
            List of meter indices that match at least one variation
        """
        result = list(indices)  # Copy the list
        
        for meter_idx in indices:
            # Get meter pattern based on index
            if meter_idx < NUM_METERS:
                meter = METERS[meter_idx].replace("/", "")
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                meter = METERS_VARIED[meter_idx - NUM_METERS].replace("/", "")
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                meter = RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS].replace("/", "")
            else:
                # Invalid index, skip
                continue
            
            # Create 4 variations
            meter1 = meter.replace("+", "")
            meter2 = meter.replace("+", "") + "-"
            meter3 = meter.replace("+", "-") + "-"
            meter4 = meter.replace("+", "-")
            
            # Flags for each variation (True = mismatch, False = match)
            # In C#, flag=True means mismatch, so we invert the logic
            flag1 = False
            flag2 = False
            flag3 = False
            flag4 = False
            
            # Variation 1: Original meter
            if len(meter1) == len(code):
                for j in range(len(meter1)):
                    met = meter1[j]
                    cd = code[j]
                    if met == '-':
                        if cd == '-' or cd == 'x':
                            pass  # Match
                        else:
                            flag1 = True  # Mismatch
                            break
                    elif met == '=':
                        if cd == '=' or cd == 'x':
                            pass  # Match
                        else:
                            flag1 = True  # Mismatch
                            break
            else:
                flag1 = True  # Length mismatch
            
            # Variation 2: meter2
            if len(meter2) == len(code):
                for j in range(len(meter2)):
                    met = meter2[j]
                    cd = code[j]
                    if met == '-':
                        if cd == '-' or cd == 'x':
                            pass  # Match
                        else:
                            flag2 = True  # Mismatch
                            break
                    elif met == '=':
                        if cd == '=' or cd == 'x':
                            pass  # Match
                        else:
                            flag2 = True  # Mismatch
                            break
            else:
                flag2 = True  # Length mismatch
            
            # Variation 3: meter3
            if len(meter3) == len(code):
                for j in range(len(meter3)):
                    met = meter3[j]
                    cd = code[j]
                    if met == '-':
                        if cd == '-' or cd == 'x':
                            pass  # Match
                        else:
                            flag3 = True  # Mismatch
                            break
                    elif met == '=':
                        if cd == '=' or cd == 'x':
                            pass  # Match
                        else:
                            flag3 = True  # Mismatch
                            break
            else:
                flag3 = True  # Length mismatch
            
            # Variation 4: meter4
            if len(meter4) == len(code):
                for j in range(len(meter4)):
                    met = meter4[j]
                    cd = code[j]
                    if met == '-':
                        if cd == '-' or cd == 'x':
                            pass  # Match
                        else:
                            flag4 = True  # Mismatch
                            break
                    elif met == '=':
                        if cd == '=' or cd == 'x':
                            pass  # Match
                        else:
                            flag4 = True  # Mismatch
                            break
            else:
                flag4 = True  # Length mismatch
            
            # Remove meter if all variations mismatch
            if flag1 and flag2 and flag3 and flag4:
                result.remove(meter_idx)
        
        return result
    
    def _traverse(self, scn: scanPath) -> List[scanPath]:
        """
        Regular traversal of the code tree for pattern matching.
        
        This method recursively traverses the tree, checking each node against
        meter patterns. It filters out meters that don't match and continues
        traversal only for matching paths.
        
        Args:
            scn: Current scanPath containing meter indices and location path
            
        Returns:
            List of scanPath objects representing matching paths through the tree
        """
        main_list: List[scanPath] = []
        
        if len(scn.meters) == 0:
            return main_list
        
        if len(self.children) > 0:
            # Build tentative code from current path
            code = ""
            for i in range(len(scn.location)):
                code += scn.location[i].code
            
            # Check each child against meters
            for k in range(len(self.children)):
                flag = False
                tentative_code = code
                word_code = self.children[k].location.code
                indices = list(scn.meters)  # Copy meter indices
                num_indices = len(scn.meters)
                
                # Check each meter index
                for i in range(num_indices):
                    meter_idx = scn.meters[i]
                    
                    if meter_idx < NUM_METERS:
                        # Regular meter
                        if not self._is_match(METERS[meter_idx], tentative_code, word_code):
                            # Remove meter index that doesn't match
                            if meter_idx in indices:
                                indices.remove(meter_idx)
                        else:
                            flag = True
                    elif meter_idx < NUM_METERS + NUM_VARIED_METERS and meter_idx >= NUM_METERS:
                        # Varied meter
                        if not self._is_match(METERS_VARIED[meter_idx - NUM_METERS], tentative_code, word_code):
                            # Remove meter index that doesn't match
                            if meter_idx in indices:
                                indices.remove(meter_idx)
                        else:
                            flag = True
                    elif meter_idx < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS and meter_idx >= NUM_METERS + NUM_VARIED_METERS:
                        # Rubai meter
                        if not self._is_match(RUBAI_METERS[meter_idx - NUM_METERS - NUM_VARIED_METERS], tentative_code, word_code):
                            # Remove meter index that doesn't match
                            if meter_idx in indices:
                                indices.remove(meter_idx)
                        else:
                            flag = True
                
                # If at least one meter matches, continue traversal
                if flag:
                    scpath = scanPath()
                    scpath.meters = indices
                    for i in range(len(scn.location)):
                        scpath.location.append(scn.location[i])
                    scpath.location.append(self.children[k].location)
                    
                    # Recursively traverse child
                    temp = self.children[k]._traverse(scpath)
                    for i in range(len(temp)):
                        main_list.append(temp[i])
            
            return main_list
        else:
            # Tree leaf - check final code length
            code = ""
            for i in range(len(scn.location)):
                code += scn.location[i].code
            
            # Filter meters by code length
            met = self._check_code_length(code, scn.meters)
            if len(met) != 0:
                scn.meters = met
                sp = [scn]
                return sp
            else:
                return []
    
    def find_meter(self, meters: Optional[List[int]] = None) -> List[scanPath]:
        """
        Find matching meters using tree traversal.
        
        This is the main entry point for meter matching. It builds a scanPath
        from the tree structure and traverses it to find matching meters.
        
        Args:
            meters: Optional list of meter indices to check. If None or empty,
                   all meters are checked. Special values:
                   - [-2]: Check only rubai meters
                   - Contains -1: Also use PatternTree for additional matches
        
        Returns:
            List of scanPath objects representing matching paths through the tree
        """
        flag = False
        indices: List[int] = []
        
        # Determine meter indices to check
        if meters is None or len(meters) == 0:
            # No meters specified - add all meters
            # First add meters with usage == 1
            for i in range(NUM_METERS):
                if USAGE[i] == 1:
                    indices.append(i)
            # Then add meters with usage == 0
            for i in range(NUM_METERS):
                if USAGE[i] == 0:
                    indices.append(i)
            # Finally add rubai meters
            for i in range(NUM_METERS, NUM_METERS + NUM_RUBAI_METERS):
                indices.append(i)
        else:
            if meters[0] == -2:
                # Special case: only rubai meters
                for i in range(NUM_METERS, NUM_METERS + NUM_RUBAI_METERS):
                    indices.append(i)
            else:
                # Add all non--1 meters, set flag if -1 found
                for meter_idx in meters:
                    if meter_idx != -1:
                        indices.append(meter_idx)
                    else:
                        flag = True
        
        # Create root scanPath
        main_list: List[scanPath] = []
        scn = scanPath()
        scn.meters = indices
        # Add root location
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        # Call appropriate traversal method based on mode
        if self.fuzzy:
            # Fuzzy matching traversal (to be implemented)
            # main_list = self._traverse_fuzzy(scn)
            main_list = []  # Placeholder until _traverse_fuzzy is implemented
        elif self.free_verse:
            # Free verse traversal (to be implemented)
            # main_list = self._traverse_free_verse(scn)
            main_list = []  # Placeholder until _traverse_free_verse is implemented
        else:
            # Regular traversal
            main_list = self._traverse(scn)
            
            # If flag is set or meters was empty, also use PatternTree for additional matches
            # TODO: Implement PatternTree integration when PatternTree class is available
            # This will call _get_code() to extract all code paths, build PatternTree,
            # call is_match(), compress results, and add to main_list
            if flag or (meters is None or len(meters) == 0):
                # PatternTree integration will be added here in a future phase
                # For now, we only use regular traversal results
                pass
        
        return main_list
    
    def _get_code(self, scn: scanPath) -> List[scanPath]:
        """
        Extract all code paths from the tree.
        
        This method recursively traverses the tree and collects all complete
        paths (from root to leaf) as scanPath objects. This is used for
        PatternTree integration.
        
        Args:
            scn: Current scanPath containing location path
        
        Returns:
            List of scanPath objects representing all paths through the tree
        """
        main_list: List[scanPath] = []
        
        if len(self.children) > 0:
            # Not a leaf - recursively get codes from children
            for k in range(len(self.children)):
                scpath = scanPath()
                # Copy current location path
                for i in range(len(scn.location)):
                    scpath.location.append(scn.location[i])
                # Add current child location
                scpath.location.append(self.children[k].location)
                
                # Recursively get codes from child
                temp = self.children[k]._get_code(scpath)
                for i in range(len(temp)):
                    main_list.append(temp[i])
        else:
            # Tree leaf - return the current path
            main_list.append(scn)
        
        return main_list
    
    def _compress_list(self, lst: List[scanPath]) -> List[scanPath]:
        """
        Compress a list of scanPath objects by merging locations from the same word.
        
        This method processes scanPath objects and merges consecutive locations
        that belong to the same word into a single location with combined code.
        This is used for PatternTree result processing.
        
        Args:
            lst: List of scanPath objects to compress
        
        Returns:
            List of compressed scanPath objects
        """
        result: List[scanPath] = []
        
        for i in range(len(lst)):
            sc = scanPath()
            sc.meters = lst[i].meters
            
            code = ""
            j = 0
            
            # Process all but the last location
            for j in range(len(lst[i].location) - 1):
                if j == 0:
                    # First element (root) - add as is
                    L = codeLocation()
                    L.code_ref = -1
                    L.word = "root"
                    L.word_ref = -1
                    L.code = ""
                    sc.location.append(L)
                    code = ""
                
                word_ref = lst[i].location[j].word_ref
                # Check if next location is from the same word
                if word_ref == lst[i].location[j + 1].word_ref:
                    # Same word - accumulate code
                    code += lst[i].location[j].code
                else:
                    # Different word - create new location with accumulated code
                    cL = codeLocation()
                    cL.code_ref = lst[i].location[j].code_ref
                    cL.word = lst[i].location[j].word
                    cL.word_ref = lst[i].location[j].word_ref
                    code += lst[i].location[j].code
                    cL.code = code
                    code = ""
                    sc.location.append(cL)
            
            # Handle last location
            # After the loop, j is len(lst[i].location) - 1 (the last index processed)
            # In C#, j-1 is checked against the last location
            if len(lst[i].location) > 1:
                # j is now len(lst[i].location) - 1 after the loop
                # Check if location[j-1] (second-to-last) has same wordRef as last location
                last_idx = len(lst[i].location) - 1
                prev_idx = last_idx - 1  # j - 1
                word_ref2 = lst[i].location[prev_idx].word_ref
                if word_ref2 == lst[i].location[last_idx].word_ref:
                    # Last location is from same word as previous - add last location's code
                    code += lst[i].location[last_idx].code
                else:
                    # Last location is from different word - use only last location's code
                    code = lst[i].location[last_idx].code
            else:
                # Only one location (shouldn't happen, but handle it)
                code = lst[i].location[0].code
            
            # Add final location
            last_idx = len(lst[i].location) - 1
            cL2 = codeLocation()
            cL2.code_ref = lst[i].location[last_idx].code_ref
            cL2.word = lst[i].location[last_idx].word
            cL2.word_ref = lst[i].location[last_idx].word_ref
            cL2.code = code
            
            sc.location.append(cL2)
            result.append(sc)
        
        return result