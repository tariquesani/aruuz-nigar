"""
Shared Urdu text helpers for rhyme modules (radeef/kafiya).
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

from aruuz.utils.araab import remove_araab

URDU_BLOCK_RE = re.compile(r"[\u0600-\u06FF]")
MULTISPACE_RE = re.compile(r"\s+")

# Canonicalization map for common Arabic/Urdu variants.
CHAR_MAP = {
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ہ",
    "ۀ": "ہ",
    "ھ": "ہ",
    "ؤ": "و",
    "أ": "ا",
    "إ": "ا",
    "ٱ": "ا",
}

# Homophone map: letters that sound identical in Urdu.
# Used for phonetic suffix matching in kafiya.
PHONETIC_MAP: dict[str, str] = {
    "ث": "س",  # both = /s/
    "ص": "س",  # both = /s/
    "ذ": "ز",  # both = /z/
    "ض": "ز",  # both = /z/
    "ظ": "ظ",  # both = /z/  (kept separate then mapped below)
    "ظ": "ز",  # both = /z/
    "ح": "ہ",  # both = /h/
    "ط": "ت",  # both = /t/
}

# End punctuation/noise for line-end matching tasks.
TRAILING_STRIP_CHARS = " ,\"'*۔،?!ؔ؟'()؛;\u200B\u200C\u200D\uFEFF.ؒ؎=ؑؓ\uFDFD\uFDFA:'[]{}"


def normalize_urdu_text(text: str) -> str:
    """Normalize Urdu text with shared canonicalization and diacritic removal."""
    if not text:
        return ""

    out = unicodedata.normalize("NFC", text)
    out = remove_araab(out)
    out = out.translate(str.maketrans(CHAR_MAP))

    # Align with existing text utility behavior:
    # ا + madd (\u0653) -> آ and ہ with hamza above normalization.
    out = re.sub("(\u0627)(\u0653)", "آ", out)
    out = re.sub("(\u06C2)", "\u06C1\u0654", out)
    out = MULTISPACE_RE.sub(" ", out).strip()
    return out


def normalize_urdu_line_for_rhyme(line: str) -> str:
    """Normalize one line for strict rhyme suffix comparisons."""
    out = normalize_urdu_text(line)
    out = out.rstrip(TRAILING_STRIP_CHARS).strip()
    out = MULTISPACE_RE.sub(" ", out).strip()
    return out


def phonetic_normalize(word: str) -> str:
    """
    Apply the Urdu homophone map to a word.

    Maps letters that are phonetically identical in Urdu to a single
    canonical form so that kafiya matching is sound-based rather than
    purely script-based.  For example:

        حال  →  ہال   (ح → ہ)
        صدا  →  سدا   (ص → س)

    Call *after* normalize_urdu_text() so CHAR_MAP variants are already
    resolved before PHONETIC_MAP is applied.
    """
    return "".join(PHONETIC_MAP.get(c, c) for c in word)


def full_normalize(word: str) -> str:
    """
    Full pipeline: script normalization → diacritic removal → phonetic mapping.

    Use this when comparing kafiya suffixes where both script differences
    (e.g. Arabic ي vs Urdu ی) and phonetic differences (e.g. ح vs ہ)
    should be treated as equivalent.
    """
    return phonetic_normalize(normalize_urdu_text(word))


def split_non_empty_lines(raw_text: str) -> List[Tuple[int, str]]:
    """Return (1-based line_number, trimmed_line) for non-empty lines."""
    out: List[Tuple[int, str]] = []
    for idx, raw_line in enumerate(raw_text.splitlines(), start=1):
        trimmed = raw_line.strip()
        if trimmed:
            out.append((idx, trimmed))
    return out


def contains_non_urdu_characters(text: str) -> bool:
    """True if text contains non-Urdu visible chars (excluding strip punctuation)."""
    for ch in text:
        if ch.isspace():
            continue
        if URDU_BLOCK_RE.match(ch):
            continue
        if ch in TRAILING_STRIP_CHARS:
            continue
        return True
    return False


def get_last_token(text: str) -> str:
    """Return last whitespace-separated token; empty string if none."""
    tokens = text.split()
    return tokens[-1] if tokens else ""


def strip_suffix_phrase(text: str, suffix_phrase: str) -> str:
    """
    Remove suffix phrase from the end of text (token-safe), then trim.
    Returns original trimmed text if suffix is absent.
    """
    if not suffix_phrase:
        return text.strip()

    base = text.strip()
    if not base.endswith(suffix_phrase):
        return base

    remainder = base[: len(base) - len(suffix_phrase)].strip()
    return remainder


__all__ = [
    "normalize_urdu_text",
    "normalize_urdu_line_for_rhyme",
    "phonetic_normalize",
    "full_normalize",
    "split_non_empty_lines",
    "contains_non_urdu_characters",
    "get_last_token",
    "strip_suffix_phrase",
    "CHAR_MAP",
    "PHONETIC_MAP",
    "TRAILING_STRIP_CHARS",
]
