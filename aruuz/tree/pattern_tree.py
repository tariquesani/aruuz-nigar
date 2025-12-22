"""
Pattern tree for state machine-based meter matching.

This module implements PatternTree class for matching scansion codes against
state machines (Hindi meters, Zamzama meters).
"""

from typing import List
from aruuz.models import codeLocation, scanPath
from aruuz.meters import (
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS
)
from aruuz.tree.state_machine import original_hindi_meter, zamzama_meter


class PatternTree:
    """
    Tree structure for pattern matching using state machines.
    
    This class builds a tree from pattern codes (e.g., from a scansion code string)
    and matches them against state machines for Hindi and Zamzama meters.
    
    Key feature: When adding a child with code "x", it expands to two children:
    - One with code "-" (short syllable)
    - One with code "=" (long syllable)
    
    Attributes:
        location: The codeLocation at this node
        children: List of child PatternTree nodes
    """
    
    def __init__(self, loc: codeLocation):
        """
        Initialize a PatternTree node.
        
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
        self.children: List['PatternTree'] = []
    
    def add_child(self, loc: codeLocation) -> None:
        """
        Recursively add a child node to the tree with 'x' code expansion.
        
        This method implements recursive tree building logic:
        - If no children exist and loc.code is "x", create two children:
          - One with code "-" (short syllable)
          - One with code "=" (long syllable)
        - If no children exist and loc.code is not "x", add the child directly
        - If children exist, recursively call add_child on all children
        
        Args:
            loc: The codeLocation to add as a child
        """
        if len(self.children) == 0:
            # No children - add new child
            if loc.code == "x":
                # Special case: "x" expands to both "-" and "="
                # Create left child with "-"
                loc_left = codeLocation(
                    code="-",
                    code_ref=loc.code_ref,
                    word_ref=loc.word_ref,
                    word=loc.word,
                    fuzzy=loc.fuzzy
                )
                child_left = PatternTree(loc_left)
                self.children.append(child_left)
                
                # Create right child with "="
                loc_right = codeLocation(
                    code="=",
                    code_ref=loc.code_ref,
                    word_ref=loc.word_ref,
                    word=loc.word,
                    fuzzy=loc.fuzzy
                )
                child_right = PatternTree(loc_right)
                self.children.append(child_right)
            else:
                # Regular code - add child directly
                child = PatternTree(loc)
                self.children.append(child)
        else:
            # Children exist - recursively add to all children
            for i in range(len(self.children)):
                self.children[i].add_child(loc)
    
    def is_match(self) -> List[scanPath]:
        """
        Main entry point for pattern matching using state machines.
        
        This method traverses the pattern tree using state machines for:
        - Original Hindi meters
        - Zamzama meters
        
        It combines results from both traversals and returns all matching paths.
        
        Returns:
            List of scanPath objects representing matching paths with detected meters
        """
        # Initialize result list
        result: List[scanPath] = []
        
        # Traverse with Original Hindi state machine
        scn_hindi = scanPath()
        a = self._traverse_original_hindi(scn_hindi, 0)
        if len(a) > 0:
            for i in range(len(a)):
                result.append(a[i])
        
        # Traverse with Zamzama state machine
        scn_zamzama = scanPath()
        a3 = self._traverse_zamzama(scn_zamzama, 0)
        if len(a3) > 0:
            for i in range(len(a3)):
                result.append(a3[i])
        
        # Note: traverseHindi is commented out in C# implementation
        # It would only be used if both original_hindi and zamzama return empty
        # For now, we skip it to match C# behavior
        
        return result
    
    def _traverse_original_hindi(self, scn: scanPath, state: int) -> List[scanPath]:
        """
        Traverse pattern tree using Original Hindi state machine.
        
        This method recursively traverses the tree, checking state transitions
        using the Original Hindi state machine. At leaf nodes, it checks
        syllable counts to determine matching meters.
        
        Args:
            scn: Current scanPath containing location path
            state: Current state machine state
            
        Returns:
            List of scanPath objects with detected meters
        """
        main_list: List[scanPath] = []
        
        # Calculate meter base offset
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        
        if len(self.children) > 0:
            # Has children - recursively traverse
            for i in range(len(self.children)):
                # Get next state from state machine
                local_state = original_hindi_meter(self.children[i].location.code, state)
                
                if local_state != -1:
                    # Valid state transition - create new scanPath
                    scpath = scanPath()
                    # Copy existing locations
                    for j in range(len(scn.location)):
                        scpath.location.append(scn.location[j])
                    # Add current child location
                    scpath.location.append(self.children[i].location)
                    
                    # Recursively traverse child
                    temp = self.children[i]._traverse_original_hindi(scpath, local_state)
                    for j in range(len(temp)):
                        main_list.append(temp[j])
        else:
            # Leaf node - check syllable count to determine meters
            count = 0
            for i in range(len(scn.location)):
                if scn.location[i].code == "=":
                    count += 2
                elif scn.location[i].code == "-":
                    count += 1
            
            # Check patterns and add matching meters
            if len(scn.location) > 0:
                last_code = scn.location[len(scn.location) - 1].code
                
                if count == 30:
                    if last_code == "=":
                        scn.meters.append(meter_base)
                        main_list.append(scn)
                elif count == 31:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base)
                            main_list.append(scn)
                elif count == 22:
                    if last_code == "=":
                        scn.meters.append(meter_base + 1)
                        main_list.append(scn)
                elif count == 23:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 1)
                            main_list.append(scn)
                elif count == 32:
                    if last_code == "=":
                        scn.meters.append(meter_base + 2)
                        main_list.append(scn)
                elif count == 33:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 2)
                            main_list.append(scn)
                elif count == 14:
                    if last_code == "=":
                        scn.meters.append(meter_base + 3)
                        main_list.append(scn)
                elif count == 15:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 3)
                            main_list.append(scn)
                elif count == 16:
                    if last_code == "=":
                        scn.meters.append(meter_base + 4)
                        main_list.append(scn)
                elif count == 17:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 4)
                            main_list.append(scn)
                elif count == 10:
                    if last_code == "=":
                        scn.meters.append(meter_base + 5)
                        main_list.append(scn)
                elif count == 11:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 5)
                            main_list.append(scn)
                elif count == 24:
                    if last_code == "=":
                        scn.meters.append(meter_base + 6)
                        main_list.append(scn)
                elif count == 25:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 6)
                            main_list.append(scn)
                elif count == 8:
                    if last_code == "=":
                        scn.meters.append(meter_base + 7)
                        main_list.append(scn)
                elif count == 9:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 7)
                            main_list.append(scn)
        
        return main_list
    
    def _traverse_zamzama(self, scn: scanPath, state: int) -> List[scanPath]:
        """
        Traverse pattern tree using Zamzama state machine.
        
        This method recursively traverses the tree, checking state transitions
        using the Zamzama state machine. At leaf nodes, it checks
        syllable counts to determine matching meters.
        
        Args:
            scn: Current scanPath containing location path
            state: Current state machine state
            
        Returns:
            List of scanPath objects with detected meters
        """
        main_list: List[scanPath] = []
        
        # Calculate meter base offset
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        
        if len(self.children) > 0:
            # Has children - recursively traverse
            for i in range(len(self.children)):
                # Get next state from state machine
                local_state = zamzama_meter(self.children[i].location.code, state)
                
                if local_state != -1:
                    # Valid state transition - create new scanPath
                    scpath = scanPath()
                    # Copy existing locations
                    for j in range(len(scn.location)):
                        scpath.location.append(scn.location[j])
                    # Add current child location
                    scpath.location.append(self.children[i].location)
                    
                    # Recursively traverse child
                    temp = self.children[i]._traverse_zamzama(scpath, local_state)
                    for j in range(len(temp)):
                        main_list.append(temp[j])
        else:
            # Leaf node - check syllable count to determine meters
            count = 0
            for i in range(len(scn.location)):
                if scn.location[i].code == "=":
                    count += 2
                elif scn.location[i].code == "-":
                    count += 1
            
            # Check patterns and add matching meters
            if len(scn.location) > 0:
                last_code = scn.location[len(scn.location) - 1].code
                
                if count == 32:
                    if last_code == "=":
                        scn.meters.append(meter_base + 8)
                        main_list.append(scn)
                elif count == 33:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 8)
                            main_list.append(scn)
                elif count == 24:
                    if last_code == "=":
                        scn.meters.append(meter_base + 9)
                        main_list.append(scn)
                elif count == 25:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 9)
                            main_list.append(scn)
                elif count == 16:
                    if last_code == "=":
                        scn.meters.append(meter_base + 10)
                        main_list.append(scn)
                elif count == 17:
                    if len(scn.location) >= 2:
                        second_last_code = scn.location[len(scn.location) - 2].code
                        if last_code == "-" and second_last_code == "=":
                            scn.meters.append(meter_base + 10)
                            main_list.append(scn)
        
        return main_list
    
    def _traverse_hindi(self, scn: scanPath, state: int) -> List[scanPath]:
        """
        Traverse pattern tree using Hindi state machine (alternative).
        
        This method is commented out in the C# implementation and would only
        be used if both original_hindi and zamzama return empty results.
        For now, we keep it as a placeholder for future use.
        
        Args:
            scn: Current scanPath containing location path
            state: Current state machine state
            
        Returns:
            List of scanPath objects with detected meters
        """
        # TODO: Implement if needed in future
        # This is commented out in C# implementation
        main_list: List[scanPath] = []
        return main_list

