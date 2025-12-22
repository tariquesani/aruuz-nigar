"""
Code tree for pattern matching.

This module implements tree structures for matching word codes to meter patterns.
"""

from typing import List, Optional
from aruuz.models import codeLocation, Lines, Words, scanPath
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS
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
