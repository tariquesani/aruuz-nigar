"""
Diacritical mark (araab) removal utilities.

This module handles removal of Urdu diacritical marks for scansion purposes.
"""

from typing import List

# Urdu diacritical marks (araab) to strip from text
ARABIC_DIACRITICS: List[str] = [
    "\u0651",  # shadd
    "\u0650",  # zer
    "\u0652",  # jazm
    "\u0656",  # khari zer
    "\u0658",  # noon ghunna
    "\u0670",  # khari zabbar
    "\u064B",  # do zabar
    "\u064D",  # do zer
    "\u064E",  # zabar
    "\u064F",  # paish
    "\u0654",  # izafat
]


def remove_araab(word: str) -> str:
    """
    Remove Urdu diacritical marks (araab) from a word.

    Args:
        word: Input word that may contain diacritical marks.

    Returns:
        The word with all diacritical marks removed. If the input is None
        or empty, returns an empty string.
    """
    if not word:
        return ""

    cleaned = word
    for mark in ARABIC_DIACRITICS:
        cleaned = cleaned.replace(mark, "")
    return cleaned


__all__ = ["remove_araab", "ARABIC_DIACRITICS"]
