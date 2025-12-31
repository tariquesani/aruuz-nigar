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
from aruuz.tree.pattern_tree import PatternTree


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
    
    def _min(self, x: int, y: int, z: int) -> int:
        """
        Find the minimum of three integers.
        
        Args:
            x: First integer
            y: Second integer
            z: Third integer
            
        Returns:
            The minimum of x, y, and z
        """
        a = x
        if x > y:
            if y > z:
                a = z
            else:
                a = y
        elif x > z:
            if y > z:
                a = z
            else:
                a = y
        else:
            a = x
        return a
    
    def _levenshtein_distance(self, pattern: str, code: str) -> int:
        """
        Calculate Levenshtein distance between pattern and code with special handling.
        
        This method calculates edit distance with special rules:
        - 'x' in code matches any character in pattern (except '~')
        - '~' in pattern matches '-' in code with zero cost
        - Other mismatches have cost 1 (deletion, insertion, or substitution)
        
        Args:
            pattern: Pattern string (may contain '~' characters)
            code: Code string (may contain 'x' characters)
            
        Returns:
            Levenshtein distance between pattern and code
        """
        m = len(pattern)
        n = len(code)
        d = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Initialize first row and column
        for i in range(m + 1):
            d[i][0] = i
        for j in range(n + 1):
            d[0][j] = j
        
        # Fill the distance matrix
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ((pattern[i - 1] == code[j - 1]) or (code[j - 1] == 'x')) and pattern[i - 1] != '~':
                    # Characters match, or code has 'x' (wildcard)
                    d[i][j] = d[i - 1][j - 1]
                else:
                    if pattern[i - 1] == '~':
                        # '~' in pattern matches '-' in code with zero cost
                        if code[j - 1] == '-':
                            d[i][j] = d[i - 1][j - 1]
                        else:
                            # Deletion, insertion, or substitution
                            d[i][j] = self._min(
                                d[i - 1][j] + 1,      # deletion
                                d[i][j - 1] + 1,      # insertion
                                d[i - 1][j - 1] + 1   # substitution
                            )
                    else:
                        # Regular mismatch - deletion, insertion, or substitution
                        d[i][j] = self._min(
                            d[i - 1][j] + 1,      # deletion
                            d[i][j - 1] + 1,      # insertion
                            d[i - 1][j - 1] + 1   # substitution
                        )
        
        return d[m][n]
    
    def _check_code_length_fuzzy(self, code: str, indices: List[int]) -> List[int]:
        """
        Filter meter indices using fuzzy matching (Levenshtein distance).
        
        This method checks if the given code matches any of the 4 variations
        of each meter pattern using Levenshtein distance. Meters are kept if
        the minimum distance across all variations is <= errorParam.
        
        The 4 variations are:
        1. Original meter with '+' removed
        2. Meter with '+' removed + '~' appended
        3. Meter with '+' replaced by '~' + '~' appended
        4. Meter with '+' replaced by '~'
        
        Args:
            code: Scansion code string (e.g., "=-=")
            indices: List of meter indices to check
            
        Returns:
            List of meter indices that match within errorParam distance
        """
        result = list(indices)  # Copy the list
        
        if len(code) == 0:
            return result
        
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
            
            # Create 4 variations (must create before removing '+' from meter)
            meter2 = meter.replace("+", "") + "~"
            meter3 = meter.replace("+", "~") + "~"
            meter4 = meter.replace("+", "~")
            meter = meter.replace("+", "")
            
            # Calculate Levenshtein distance for each variation
            flag1 = self._levenshtein_distance(meter, code)
            flag2 = self._levenshtein_distance(meter2, code)
            flag3 = self._levenshtein_distance(meter3, code)
            flag4 = self._levenshtein_distance(meter4, code)
            
            # Keep meter if minimum distance is within errorParam
            min_distance = min(flag4, self._min(flag1, flag2, flag3))
            if min_distance > self.error_param:
                result.remove(meter_idx)
        
        return result
    
    def _traverse_fuzzy(self, scn: scanPath) -> List[scanPath]:
        """
        Fuzzy traversal of the code tree for pattern matching.
        
        This method recursively traverses the tree without filtering meters
        during traversal. All children are explored, and meter filtering happens
        only at leaf nodes using Levenshtein distance.
        
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
            fuzz = 0
            for i in range(len(scn.location)):
                code += scn.location[i].code
                fuzz += scn.location[i].fuzzy
            
            # Traverse all children without filtering
            for k in range(len(self.children)):
                indices = list(scn.meters)  # Copy meter indices
                
                scpath = scanPath()
                scpath.meters = indices
                for i in range(len(scn.location)):
                    scpath.location.append(scn.location[i])
                scpath.location.append(self.children[k].location)
                
                # Recursively traverse child
                temp = self.children[k]._traverse_fuzzy(scpath)
                for i in range(len(temp)):
                    main_list.append(temp[i])
            
            return main_list
        else:
            # Tree leaf - check final code length using fuzzy matching
            code = ""
            for i in range(len(scn.location)):
                code += scn.location[i].code
            
            # Filter meters by code length using fuzzy matching
            met = self._check_code_length_fuzzy(code, scn.meters)
            if len(met) != 0:
                scn.meters = met
                sp = [scn]
                return sp
            else:
                return []
    
    def _check_meter_free_verse(self, code: str, indices: List[int]) -> List[int]:
        """
        Filter meter indices for free verse matching.
        
        This method checks if the code can be matched by any foot pattern
        from the meter. It splits the meter into feet and tries to match
        the code character by character against the feet.
        
        Args:
            code: Scansion code string (e.g., "=-=")
            indices: List of meter indices to check
            
        Returns:
            List of meter indices that match the code using foot patterns
        """
        result = list(indices)  # Copy the list
        
        if len(code) == 0:
            return result
        
        for meter_idx in indices:
            # Get meter pattern based on index
            if meter_idx < NUM_METERS:
                meter = METERS[meter_idx]
            elif meter_idx < NUM_METERS + NUM_VARIED_METERS:
                meter = METERS_VARIED[meter_idx - NUM_METERS]
            else:
                # Skip rubai meters for free verse (not in C# implementation)
                continue
            
            # Split meter into feet
            # Replace spaces, then replace '+' and '/' with spaces, then split
            residue = meter.replace(" ", "")
            residue = residue.replace("+", " ")
            residue = residue.replace("/", " ")
            feet = []
            for s in residue.split():
                # Only add unique feet
                if s not in feet:
                    feet.append(s)
            
            # Try to match code against feet
            f = True  # Flag indicating if match is successful
            j = 0
            while j < len(code):
                index = -1
                # Try each foot
                for k in range(len(feet)):
                    flag = True
                    index = k
                    # Check if foot fits at current position
                    if j + len(feet[k]) > len(code):
                        index = -1
                        flag = False
                    else:
                        # Check if code slice matches foot
                        slice_code = code[j:j + len(feet[k])]
                        for z in range(len(feet[k])):
                            if not ((slice_code[z] == feet[k][z]) or (slice_code[z] == 'x')):
                                flag = False
                                index = -1
                                break
                    
                    if flag:
                        break
                
                if index >= 0:
                    # Found matching foot - advance position
                    j = j + len(feet[index])
                else:
                    # No matching foot found
                    f = False
                    break
            
            # Remove meter if match failed
            if not f:
                result.remove(meter_idx)
        
        return result
    
    def _traverse_free_verse(self, scn: scanPath) -> List[scanPath]:
        """
        Free verse traversal of the code tree for pattern matching.
        
        This method recursively traverses the tree without filtering meters
        during traversal. All children are explored, and meter filtering happens
        only at leaf nodes using foot pattern matching.
        
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
            fuzz = 0
            for i in range(len(scn.location)):
                code += scn.location[i].code
                fuzz += scn.location[i].fuzzy
            
            # Traverse all children without filtering
            for k in range(len(self.children)):
                indices = list(scn.meters)  # Copy meter indices
                
                scpath = scanPath()
                scpath.meters = indices
                for i in range(len(scn.location)):
                    scpath.location.append(scn.location[i])
                scpath.location.append(self.children[k].location)
                
                # Recursively traverse child
                temp = self.children[k]._traverse_free_verse(scpath)
                for i in range(len(temp)):
                    main_list.append(temp[i])
            
            return main_list
        else:
            # Tree leaf - check final code length using free verse matching
            code = ""
            for i in range(len(scn.location)):
                code += scn.location[i].code
            
            # Filter meters by code length using free verse matching
            met = self._check_meter_free_verse(code, scn.meters)
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
            # Fuzzy matching traversal
            main_list = self._traverse_fuzzy(scn)
        elif self.free_verse:
            # Free verse traversal
            main_list = self._traverse_free_verse(scn)
        else:
            # Regular traversal
            main_list = self._traverse(scn)
            
            # If flag is set or meters was empty, also use PatternTree for additional matches
            if flag or (meters is None or len(meters) == 0):
                # Get all code paths from the tree
                code_paths = self._get_code(scn)
                
                # Create root codeLocation for PatternTree
                root_loc = codeLocation(
                    code="root",
                    word_ref=-1,
                    code_ref=-1,
                    word="",
                    fuzzy=0
                )
                
                # Process each path
                for path in code_paths:
                    # Create PatternTree with root location
                    p_tree = PatternTree(root_loc)
                    
                    # Character-by-character expansion
                    for j in range(len(path.location)):
                        location = path.location[j]
                        code_str = location.code
                        
                        # Process each character in the code string
                        for k in range(len(code_str)):
                            # Create new codeLocation with single character
                            char_code = code_str[k]
                            
                            # Special handling: if this is the last character of the last location
                            # and the code is "x", convert it to "="
                            if j == len(path.location) - 1 and k == len(code_str) - 1:
                                if char_code == "x":
                                    char_code = "="
                            
                            # Create character location preserving metadata
                            char_loc = codeLocation(
                                code=char_code,
                                code_ref=location.code_ref,
                                word_ref=location.word_ref,
                                word=location.word,
                                fuzzy=location.fuzzy
                            )
                            
                            # Add character location as child to PatternTree
                            p_tree.add_child(char_loc)
                    
                    # Call is_match() to get PatternTree results
                    pattern_results = p_tree.is_match()
                    
                    # If results exist, compress them and add to main_list
                    if len(pattern_results) > 0:
                        compressed_results = self._compress_list(pattern_results)
                        for result in compressed_results:
                            main_list.append(result)
        
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
            sc.meters = list(lst[i].meters)  # Copy meters list
            
            code = ""
            # Process all but the last location (j = 0 to Count-2)
            # After loop, j will be Count-1 (last valid index from range)
            j = 0
            for j in range(len(lst[i].location) - 1):
                if j == 0:
                    # First element (root) - add as is with empty code
                    L = codeLocation(
                        code="",
                        code_ref=-1,
                        word="root",
                        word_ref=-1,
                        fuzzy=0
                    )
                    sc.location.append(L)
                    code = ""
                
                word_ref = lst[i].location[j].word_ref
                # Check if next location is from the same word
                if word_ref == lst[i].location[j + 1].word_ref:
                    # Same word - accumulate code (don't add location yet)
                    code += lst[i].location[j].code
                else:
                    # Different word - create new location with accumulated code
                    code += lst[i].location[j].code
                    cL = codeLocation(
                        code=code,
                        code_ref=lst[i].location[j].code_ref,
                        word=lst[i].location[j].word,
                        word_ref=lst[i].location[j].word_ref,
                        fuzzy=lst[i].location[j].fuzzy
                    )
                    sc.location.append(cL)
                    code = ""
            
            # After loop in C#, j = Count-1 (incremented after last iteration)
            # In Python, after range(n), j = n-1, so we need j+1 to get the last index
            # But we want j to represent the last index, so we set it explicitly
            if len(lst[i].location) > 1:
                # j is currently Count-2 (last value from range), so j+1 is Count-1 (last index)
                j_last = len(lst[i].location) - 1  # Explicitly use last index
                word_ref2 = lst[i].location[j_last - 1].word_ref  # Second-to-last
                if word_ref2 == lst[i].location[j_last].word_ref:
                    # Last location is from same word as previous - add to accumulated code
                    code += lst[i].location[j_last].code
                else:
                    # Last location is from different word - use only last location's code
                    code = lst[i].location[j_last].code
            else:
                # Only one location (edge case)
                code = lst[i].location[0].code
            
            # Add final location with accumulated/selected code
            last_idx = len(lst[i].location) - 1
            cL2 = codeLocation(
                code=code,
                code_ref=lst[i].location[last_idx].code_ref,
                word=lst[i].location[last_idx].word,
                word_ref=lst[i].location[last_idx].word_ref,
                fuzzy=lst[i].location[last_idx].fuzzy
            )
            sc.location.append(cL2)
            result.append(sc)
        
        return result
    
    def visualize(self, indent: str = "", is_last: bool = True, prefix: str = "") -> str:
        """
        Generate a text-based tree visualization showing all codes and their locations.
        
        This method creates a hierarchical tree representation showing:
        - Node codes
        - Word references and words
        - Code references
        - Tree structure with branches
        
        Args:
            indent: Current indentation string
            is_last: Whether this is the last child at this level
            prefix: Prefix string for the current line
            
        Returns:
            String representation of the tree
        """
        # Build the current node representation
        if self.location.code == "root":
            node_str = "root"
        else:
            node_str = f"code='{self.location.code}' | word_ref={self.location.word_ref}"
            if self.location.word:
                node_str += f" | word='{self.location.word}'"
            node_str += f" | code_ref={self.location.code_ref}"
        
        # Create the line for this node
        if indent == "":
            # Root node
            result = f"{node_str}\n"
        else:
            # Child node
            connector = "└── " if is_last else "├── "
            result = f"{prefix}{connector}{node_str}\n"
        
        # Process children
        if len(self.children) > 0:
            # Determine new prefix and indent
            if indent != "":
                new_prefix = prefix + ("    " if is_last else "│   ")
            else:
                new_prefix = ""
            
            # Recursively visualize children
            for i, child in enumerate(self.children):
                is_last_child = (i == len(self.children) - 1)
                result += child.visualize(
                    indent=indent + "    ",
                    is_last=is_last_child,
                    prefix=new_prefix
                )
        
        return result
    
    def get_all_paths(self) -> List[List[codeLocation]]:
        """
        Get all paths from root to leaf as lists of codeLocation objects.
        
        Returns:
            List of paths, where each path is a list of codeLocation objects
            from root to leaf
        """
        paths = []
        
        if len(self.children) == 0:
            # Leaf node - return path with just this node
            return [[self.location]]
        
        # For each child, get its paths and prepend this node
        for child in self.children:
            child_paths = child.get_all_paths()
            for path in child_paths:
                # Skip root in paths (it's redundant)
                if self.location.code != "root":
                    paths.append([self.location] + path)
                else:
                    paths.append(path)
        
        return paths
    
    def get_summary(self) -> dict:
        """
        Get a summary of the tree structure.
        
        Returns:
            Dictionary containing:
            - total_nodes: Total number of nodes in the tree
            - total_paths: Total number of paths from root to leaf
            - max_depth: Maximum depth of the tree
            - word_codes: Dictionary mapping word_ref to list of codes
        """
        def count_nodes(node: 'CodeTree') -> int:
            count = 1
            for child in node.children:
                count += count_nodes(child)
            return count
        
        def get_max_depth(node: 'CodeTree', depth: int = 0) -> int:
            if len(node.children) == 0:
                return depth
            return max([get_max_depth(child, depth + 1) for child in node.children])
        
        def collect_word_codes(node: 'CodeTree', word_codes: dict) -> None:
            if node.location.code != "root":
                word_ref = node.location.word_ref
                if word_ref not in word_codes:
                    word_codes[word_ref] = []
                code_info = {
                    'code': node.location.code,
                    'code_ref': node.location.code_ref,
                    'word': node.location.word
                }
                if code_info not in word_codes[word_ref]:
                    word_codes[word_ref].append(code_info)
            
            for child in node.children:
                collect_word_codes(child, word_codes)
        
        word_codes = {}
        collect_word_codes(self, word_codes)
        
        return {
            'total_nodes': count_nodes(self),
            'total_paths': len(self.get_all_paths()),
            'max_depth': get_max_depth(self),
            'word_codes': word_codes
        }
    
    def __str__(self) -> str:
        """String representation of the tree."""
        return self.visualize()
    
    def __repr__(self) -> str:
        """Detailed representation of the tree."""
        summary = self.get_summary()
        return (f"CodeTree(nodes={summary['total_nodes']}, "
                f"paths={summary['total_paths']}, "
                f"depth={summary['max_depth']})")