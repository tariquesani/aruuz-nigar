"""
Data models for scansion processing.

This module contains data classes for words, lines, and output structures.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Words:
    """
    Represents a word in Urdu poetry with its scansion information.
    
    Attributes:
        word: The Urdu word text
        code: List of scansion codes (e.g., "=", "-", "x")
        taqti: List of taqti (scansion breakdown) strings
        muarrab: List of words with diacritical marks
        length: Length of the word (without diacritics)
        id: List of database IDs (for future database integration)
        is_varied: List of boolean flags indicating if word has variations
        error: Boolean flag indicating if word processing had errors
        modified: Boolean flag indicating if word was modified during processing
        language: List of language classifications
        taqti_word_graft: List of taqti word graft strings
        breakup: List of word breakup strings
    """
    word: str = ""
    code: List[str] = field(default_factory=list)
    taqti: List[str] = field(default_factory=list)
    muarrab: List[str] = field(default_factory=list)
    length: int = 0
    id: List[int] = field(default_factory=list)
    is_varied: List[bool] = field(default_factory=list)
    error: bool = False
    modified: bool = False
    language: List[str] = field(default_factory=list)
    taqti_word_graft: List[str] = field(default_factory=list)
    breakup: List[str] = field(default_factory=list)

    def __copy__(self):
        """Create a copy of the Words object."""
        return Words(
            word=self.word,
            code=self.code.copy(),
            taqti=self.taqti.copy(),
            muarrab=self.muarrab.copy(),
            length=self.length,
            id=self.id.copy(),
            is_varied=self.is_varied.copy(),
            error=self.error,
            modified=self.modified,
            language=self.language.copy(),
            taqti_word_graft=self.taqti_word_graft.copy(),
            breakup=self.breakup.copy()
        )


@dataclass
class Feet:
    """
    Represents a foot (rukn) in Urdu poetry meter.
    
    Attributes:
        foot: Foot name in Urdu
        code: Foot pattern code
        words: Words that make up this foot
    """
    foot: str = ""
    code: str = ""
    words: str = ""


@dataclass
class codeLocation:
    """
    Represents a location in the scansion code tree.
    
    Attributes:
        code: Scansion code at this location
        word_ref: Reference to word index
        code_ref: Reference to code index
        word: Word text at this location
        fuzzy: Fuzzy matching score (for future fuzzy matching)
    """
    code: str = ""
    word_ref: int = -1
    code_ref: int = -1
    word: str = ""
    fuzzy: int = 0


class scanPath:
    """
    Represents a path through the scansion code tree.
    
    Attributes:
        location: List of codeLocation objects
        meters: List of meter indices that match this path
    """
    def __init__(self):
        self.location: List[codeLocation] = []
        self.meters: List[int] = []


@dataclass
class scanOutput:
    """
    Represents the output of scansion analysis for a line of poetry.
    
    Attributes:
        original_line: Original line of poetry text
        words: List of Words objects in this line
        feet_list: List of Feet objects
        word_taqti: List of taqti codes for each word
        word_muarrab: List of muarrab forms for each word
        feet: Feet breakdown as string
        meter_name: Name of the identified meter
        id: Internal ID for this scan output
        identifier: External identifier (e.g., poetry ID)
        poet: Poet name (optional)
        title: Poem title (optional)
        text: Full poem text (optional)
        url: URL reference (optional)
        num_lines: Number of lines in the poem
    """
    original_line: str = ""
    words: List[Words] = field(default_factory=list)
    feet_list: List[Feet] = field(default_factory=list)
    word_taqti: List[str] = field(default_factory=list)
    word_muarrab: List[str] = field(default_factory=list)
    feet: str = ""
    meter_name: str = ""
    id: int = 0
    identifier: int = -1
    poet: str = ""
    title: str = ""
    text: str = ""
    url: str = ""
    num_lines: int = 0


@dataclass
class scanOutputFuzzy:
    """
    Represents fuzzy scansion output (for future fuzzy matching feature).
    
    Attributes:
        original_line: Original line of poetry text
        words: List of Words objects
        error: List of boolean flags indicating errors
        word_taqti: List of taqti codes
        original_taqti: List of original taqti codes
        feet: Feet breakdown
        meter_name: Name of the identified meter
        meter_syllables: List of meter syllable patterns
        code_syllables: List of code syllable patterns
        score: Matching score
        id: Internal ID
        identifier: External identifier
        hidden: Boolean flag for hiding this result
    """
    original_line: str = ""
    words: List[Words] = field(default_factory=list)
    error: List[bool] = field(default_factory=list)
    word_taqti: List[str] = field(default_factory=list)
    original_taqti: List[str] = field(default_factory=list)
    feet: str = ""
    meter_name: str = ""
    meter_syllables: List[str] = field(default_factory=list)
    code_syllables: List[str] = field(default_factory=list)
    score: int = 10
    id: int = 0
    identifier: int = -1
    hidden: bool = False


class Lines:
    """
    Represents a line of Urdu poetry.
    
    Attributes:
        original_line: Original line text
        words_list: List of Words objects in this line
    """
    def __init__(self, line: str):
        """
        Initialize a Lines object from a line of poetry.
        
        Note: Full text processing will be implemented in Step 5
        after utility functions are created. This is a basic structure.
        
        Args:
            line: Line of Urdu poetry text
        """
        # Store original line
        self.original_line = line
        
        # Initialize words list
        # Full parsing will be implemented in Step 5 using utils/text.py
        self.words_list: List[Words] = []
        
        # Basic word splitting (will be enhanced in Step 5)
        # For now, just create placeholder structure
        if line.strip():
            # Simple split by spaces - will be replaced with proper parsing
            words = line.split()
            for word_text in words:
                if word_text.strip():
                    word = Words()
                    word.word = word_text.strip()
                    word.length = len(word_text.strip())  # Temporary, will use araab removal
                    if word.length > 0:
                        self.words_list.append(word)
