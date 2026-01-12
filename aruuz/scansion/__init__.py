"""
Aruuz Scansion Module

Public API for the scansion package. Exports the main Scansion class
and key utility functions for backward compatibility.
"""

# Main class export
from .core import Scansion

# Deprecated functions (kept for backward compatibility)
from .deprecated import is_match, check_code_length

# Word analysis utilities
from .word_analysis import (
    is_vowel_plus_h,
    is_muarrab,
    is_izafat,
    is_consonant_plus_consonant,
    locate_araab,
    contains_noon,
    remove_tashdid
)

# Code assignment
from .code_assignment import compute_scansion

# Length scanners
from .length_scanners import (
    length_one_scan,
    length_two_scan,
    length_three_scan,
    length_four_scan,
    length_five_scan,
    noon_ghunna
)

__all__ = [
    'Scansion',
    'is_match',
    'check_code_length',
    'is_vowel_plus_h',
    'is_muarrab',
    'is_izafat',
    'is_consonant_plus_consonant',
    'locate_araab',
    'contains_noon',
    'remove_tashdid',
    'compute_scansion',
    'length_one_scan',
    'length_two_scan',
    'length_three_scan',
    'length_four_scan',
    'length_five_scan',
    'noon_ghunna'
]
