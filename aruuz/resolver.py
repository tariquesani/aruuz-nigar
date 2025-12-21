"""
Word code resolver module for Aruuz.

Provides WordCodeResolver class that coordinates multiple strategies for resolving
word scansion codes (database lookup and heuristics).
"""

import logging
from typing import Optional
from aruuz.models import Words
from aruuz.scansion import Scansion
from aruuz.utils.araab import remove_araab

# Set up logger for debug statements
logger = logging.getLogger(__name__)


class WordCodeResolver:
    """
    Resolves word codes using multiple strategies in priority order.
    
    Strategy 1: Database lookup (if available)
    Strategy 2: Heuristics (fallback)
    
    This class keeps strategy selection logic separate from the heuristics engine.
    """
    
    def __init__(self, db_lookup=None):
        """
        Initialize resolver with optional database lookup.
        
        Args:
            db_lookup: Optional WordLookup instance for database strategy
        """
        self.db_lookup = db_lookup
        # Create internal Scansion instance for heuristic strategy
        self._heuristic_scansion = Scansion()
    
    def resolve(self, word: Words) -> Words:
        """
        Resolve word code using available strategies in order.
        
        Args:
            word: Words object to resolve code for
            
        Returns:
            Words object with code assigned
        """
        logger.debug(f"[DEBUG] WordCodeResolver.resolve() called with word: '{word.word}'")
        
        # If word already has codes, return as is
        if len(word.code) > 0:
            logger.debug(f"[DEBUG] WordCodeResolver.resolve() word already has codes, returning early")
            return word
        
        # Strategy 1: Try database lookup first (if available)
        if self.db_lookup:
            logger.debug(f"[DEBUG] WordCodeResolver.resolve() db_lookup is available, trying database lookup")
            try:
                word = self.db_lookup.find_word(word)
                
                # If database lookup found results
                if len(word.id) > 0:
                    logger.debug(f"[DEBUG] WordCodeResolver.resolve() database lookup found {len(word.id)} result(s), applying variations")
                    # Apply special 3-character word handling
                    word = self._apply_db_word_variations(word)
                    return word
                else:
                    logger.debug(f"[DEBUG] WordCodeResolver.resolve() database lookup returned no results, falling back to heuristics")
            except Exception as e:
                # On any DB error, fall back to heuristics
                logger.debug(f"[DEBUG] WordCodeResolver.resolve() database lookup raised exception: {e}, falling back to heuristics")
                pass
        else:
            logger.debug(f"[DEBUG] WordCodeResolver.resolve() db_lookup is None, skipping database lookup")
        
        # Strategy 2: Fallback to heuristics
        logger.debug(f"[DEBUG] WordCodeResolver.resolve() using heuristics fallback")
        return self._heuristic_scansion.word_code(word)
    
    def _apply_db_word_variations(self, word: Words) -> Words:
        """
        Apply special 3-character word handling for DB results.
        
        Mirrors C# logic (lines 1846-1869) for post-processing database results.
        
        For 3-character words ending in 'ا' (alif):
        - If word starts with 'آ': add alternative code "==" or "=x" if not already present
        - If word doesn't start with 'آ': add alternative code "-=" or "-x" if not already present
        
        Args:
            word: Words object from database lookup
            
        Returns:
            Words object with additional code variations if applicable
        """
        # Remove araab and special characters (ھ \u06BE and ں \u06BA) for scansion purposes
        # C#: string subString = Araab.removeAraab(wrd.word.Replace("\u06BE", "").Replace("\u06BA", ""));
        sub_string = word.word.replace("\u06BE", "").replace("\u06BA", "")
        sub_string = remove_araab(sub_string)
        
        # C#: if (subString.Length == 3)
        if len(sub_string) == 3:
            # C#: if(subString[2] == 'ا')
            if sub_string[2] == 'ا':  # Third character is alif
                # C#: if (subString[0] == 'آ')
                if sub_string[0] == 'آ':  # First character is alif madd
                    # C#: if (!wrd.code[0].Equals("==") && !wrd.code[0].Equals("=x"))
                    if len(word.code) > 0 and word.code[0] != "==" and word.code[0] != "=x":
                        # C#: wrd.id.Add(-1);
                        # C#: wrd.code.Add("==");
                        word.id.append(-1)
                        word.code.append("==")
                else:  # First character is not alif madd
                    # C#: if (!wrd.code[0].Equals("-=") && !wrd.code[0].Equals("-x"))
                    if len(word.code) > 0 and word.code[0] != "-=" and word.code[0] != "-x":
                        # C#: wrd.id.Add(-1);
                        # C#: wrd.code.Add("-=");
                        word.id.append(-1)
                        word.code.append("-=")
        
        return word

