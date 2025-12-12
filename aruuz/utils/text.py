"""
Text processing utilities.

This module handles cleaning and processing of Urdu text.
"""

import re
from typing import Pattern

# Patterns for replacements
_ALEF_MAD_PATTERN: Pattern[str] = re.compile("(\u0627)(\u0653)")  # ا + madd -> آ
_HEH_GOAL_PATTERN: Pattern[str] = re.compile("(\u06C2)")  # ہ with hamza above -> ۂ

# Characters to strip from lines (punctuation and noise)
_STRIP_CHARS = [
    ",", "\"", "*", "'", "-", "۔", "،", "?", "!", "ؔ", "؟", "‘", "(", ")", "؛",
    ";", "\u200B", "\u200C", "\u200D", "\uFEFF", ".", "ؒ", "؎", "=", "ؑ", "ؓ",
    "\uFDFD", "\uFDFA", ":", "’"
]


def clean_word(word: str) -> str:
    """
    Clean an Urdu word by applying character-level replacements.

    - Replace final ئ with یٔ
    - Replace ا + madd (\u0653) with آ
    - Replace \u06C2 with \u06C1\u0654
    """
    if not word:
        return ""

    cleaned = word

    # If word ends with ئ, replace with یٔ
    if cleaned.endswith("ئ"):
        cleaned = cleaned[:-1] + "یٔ"

    # Apply regex replacements
    cleaned = _ALEF_MAD_PATTERN.sub("آ", cleaned)
    cleaned = _HEH_GOAL_PATTERN.sub("\u06C1\u0654", cleaned)  # ۂ

    return cleaned


def clean_line(line: str) -> str:
    """
    Clean a line of Urdu text by removing punctuation and zero-width characters.

    Args:
        line: Input line of Urdu text

    Returns:
        Cleaned line with unwanted characters removed.
    """
    if not line:
        return ""

    cleaned = line
    for ch in _STRIP_CHARS:
        cleaned = cleaned.replace(ch, "")

    return cleaned


__all__ = ["clean_word", "clean_line"]

