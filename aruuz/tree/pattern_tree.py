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
        # TODO: Implement state machine traversal in next phase
        # This will call StateMachine.original_hindi_meter() for state transitions
        # and check syllable counts at leaf nodes to determine meters
        main_list: List[scanPath] = []
        
        # Placeholder implementation - will be completed in pattern_tree_state_machine phase
        # For now, return empty list to allow core structure to compile
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
        # TODO: Implement state machine traversal in next phase
        # This will call StateMachine.zamzama_meter() for state transitions
        # and check syllable counts at leaf nodes to determine meters
        main_list: List[scanPath] = []
        
        # Placeholder implementation - will be completed in pattern_tree_state_machine phase
        # For now, return empty list to allow core structure to compile
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

