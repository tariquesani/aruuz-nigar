"""
Data models for scansion processing.

This module contains data classes for words, lines, and output structures.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from aruuz.utils.text import clean_line, clean_word
from aruuz.utils.araab import remove_araab


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
        is_dominant: True if this is the dominant meter from crunch()
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
    is_dominant: bool = False  # True if this is the dominant meter from crunch()


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
        
        This method:
        1. Cleans the line using clean_line() to remove punctuation
        2. Splits the line into words by comma and space delimiters
        3. Cleans each word using clean_word() to apply character replacements
        4. Creates Words objects with cleaned words and calculates length
        
        Args:
            line: Line of Urdu poetry text
        """
        # Clean the line to remove punctuation and zero-width characters
        cleaned_line = clean_line(line)
        
        # Store original line (cleaned)
        self.original_line = cleaned_line
        
        # Initialize words list
        self.words_list: List[Words] = []
        
        # Split by comma and space delimiters (matching C# behavior)
        # C# uses: originalLine.Split(delimiters, StringSplitOptions.RemoveEmptyEntries)
        import re
        delimiters_pattern = r'[, ]+'  # Match comma or space, one or more times
        words_raw = re.split(delimiters_pattern, cleaned_line)
        
        # Process each word
        for word_text in words_raw:
            word_text = word_text.strip()
            if word_text:
                # Clean the word (applies character replacements)
                # This matches the C# Replace() method
                cleaned_word = clean_word(word_text)
                
                # Create Words object
                word = Words()
                word.word = cleaned_word
                
                # Calculate length after removing diacritics
                # This matches: wrd.length = Araab.removeAraab(wrd.word).Length
                word.length = len(remove_araab(cleaned_word))
                
                # Only add words with length > 0
                # This matches: if (wrd.length > 0) wordsList.Add(wrd);
                if word.length > 0:
                    self.words_list.append(word)
