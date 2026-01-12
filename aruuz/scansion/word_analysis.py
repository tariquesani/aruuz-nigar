"""
Word Analysis Utilities

Pure utility functions for word classification and analysis.
No classes, no state dependencies.
"""

from aruuz.utils.araab import ARABIC_DIACRITICS


def is_vowel_plus_h(char: str) -> bool:
    """
    Check if character is a vowel+h pattern (flexible syllable).
    
    Characters that indicate flexible syllables: ا،ی،ے،و،ہ،ؤ
    
    Args:
        char: Single character to check
        
    Returns:
        True if character is a vowel+h pattern, False otherwise
    """
    return char in ['ا', 'ی', 'ے', 'و', 'ہ', 'ؤ']


def is_muarrab(word: str) -> bool:
    """
    Check if word has diacritical marks (muarrab).
    
    Args:
        word: Word to check
        
    Returns:
        True if word contains any diacritical marks, False otherwise
    """
    for char in word:
        if char in ARABIC_DIACRITICS:
            return True
    return False


def is_izafat(word: str) -> bool:
    """
    Check if last character is izafat marker.
    
    Checks if the last character is:
    - ARABIC_DIACRITICS[1] (zer, \u0650)
    - ARABIC_DIACRITICS[10] (izafat, \u0654)
    - \u06C2 (ۂ)
    
    Args:
        word: Word to check
        
    Returns:
        True if last character is an izafat marker, False otherwise
    """
    if not word or len(word) == 0:
        return False
    
    last_char = word[-1]
    return (last_char == ARABIC_DIACRITICS[1] or 
            last_char == ARABIC_DIACRITICS[10] or 
            last_char == '\u06C2')


def is_consonant_plus_consonant(word: str) -> bool:
    """
    Check if positions 0 and 1 are both consonants (not ا،ی،ے،ہ).
    
    This function checks if both the first and second characters of the word
    are consonants, meaning they are NOT one of the vowel characters:
    ا (alif), ی (ye), ے (ye barree), or ہ (heh).
    
    Args:
        word: Word to check
        
    Returns:
        True if both positions 0 and 1 are consonants, False otherwise.
        Returns False if word length is less than 2.
    """
    if not word or len(word) < 2:
        return False
    
    # Check if position 1 is NOT a vowel
    if not (word[1] == 'ا' or word[1] == 'ی' or word[1] == 'ے' or word[1] == 'ہ'):
        # Check if position 0 is NOT a vowel
        if not (word[0] == 'ا' or word[0] == 'ی' or word[0] == 'ے' or word[0] == 'ہ'):
            return True
        else:
            return False
    else:
        return False


def remove_tashdid(word: str) -> str:
    """
    Remove shadd diacritic by replacing it with appropriate diacritics.
    
    This function processes shadd (ARABIC_DIACRITICS[0]) and replaces it
    with appropriate diacritics (jazm + char + paish) based on context.
    Only processes words that contain diacritical marks (muarrab).
    
    Args:
        word: Word that may contain shadd diacritic
        
    Returns:
        Modified word with shadd replaced, or original word if not muarrab
    """
    # Only process if word is muarrab (has diacritics)
    if not is_muarrab(word):
        return word
    
    wrd = ""
    for i in range(len(word)):
        if word[i] == ARABIC_DIACRITICS[0]:  # shadd
            if i - 2 >= 0:  # There are at least 2 characters before this shadd
                # Check if character at i-2 is NOT a diacritic
                if word[i - 2] not in ARABIC_DIACRITICS:
                    # Check if character at i-1 is NOT a diacritic
                    if word[i - 1] not in ARABIC_DIACRITICS:
                        # Remove last character from wrd, then add replacement
                        if len(wrd) > 0:
                            wrd = wrd[:-1]
                        wrd += word[i - 1] + ARABIC_DIACRITICS[2] + word[i - 1] + ARABIC_DIACRITICS[8]
                    else:
                        # word[i-1] IS a diacritic
                        # Remove last 2 characters from wrd, then add replacement
                        if len(wrd) >= 2:
                            wrd = wrd[:-2]
                        wrd += word[i - 2] + ARABIC_DIACRITICS[2] + word[i - 2] + ARABIC_DIACRITICS[8]
                else:
                    # word[i-2] IS a diacritic
                    wrd += ARABIC_DIACRITICS[2] + word[i - 1] + ARABIC_DIACRITICS[8]
            else:
                # i - 2 < 0, not enough characters before shadd
                # Need at least i-1 >= 0 to access word[i-1]
                if i - 1 >= 0:
                    wrd += ARABIC_DIACRITICS[2] + word[i - 1] + ARABIC_DIACRITICS[8]
        else:
            # Not a shadd, add character as-is
            wrd += word[i]
    
    return wrd


def locate_araab(word: str) -> str:
    """
    Extract diacritical marks positions from a word.
    
    Returns a string where each position corresponds to a character,
    with the diacritical mark if present, or space if absent.
    
    Args:
        word: Word with potential diacritical marks
        
    Returns:
        String of diacritical marks aligned with character positions
    """
    loc = ""
    i = 0
    while i < len(word):
        if i < len(word) - 1:
            # Check if next character is a diacritical mark
            if word[i + 1] in ARABIC_DIACRITICS:
                loc += word[i + 1]
                i += 2
            else:
                loc += " "
                i += 1
        else:
            loc += " "
            i += 1
    return loc


def contains_noon(word: str) -> bool:
    """
    Check if word contains noon (ن) character (excluding last position).
    
    Args:
        word: Word to check
        
    Returns:
        True if word contains noon before the last character
    """
    if len(word) > 1:
        for i in range(len(word) - 1):
            if word[i] == 'ن':
                return True
    return False
