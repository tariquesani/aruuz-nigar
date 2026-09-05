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

# Explanation builder
from .explanation_builder import ExplanationBuilder

# Length scanners
from .length_scanners import (
    length_one_scan,
    length_two_scan,
    length_three_scan,
    length_four_scan,
    length_five_scan,
    noon_ghunna
)

# Noon keep/drop model
from .noon_model import (
    DROP,
    EITHER,
    KEEP,
    NoonDecision,
    candidate_noon_positions,
    classify_noon,
    drop_noon,
    has_jazm,
    is_protected_noon,
    medial_noon_positions
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
    'noon_ghunna',
    'ExplanationBuilder',
    'KEEP',
    'DROP',
    'EITHER',
    'NoonDecision',
    'candidate_noon_positions',
    'classify_noon',
    'drop_noon',
    'has_jazm',
    'is_protected_noon',
    'medial_noon_positions'
]
