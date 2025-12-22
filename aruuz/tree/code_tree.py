"""
Code tree for pattern matching.

This module implements tree structures for matching word codes to meter patterns.
"""

from typing import List, Optional
from aruuz.models import codeLocation, Lines, Words


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
