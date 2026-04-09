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

# End punctuation/noise for line-end matching tasks.
TRAILING_STRIP_CHARS = " ,\"'*۔،?!ؔ؟‘()؛;\u200B\u200C\u200D\uFEFF.ؒ؎=ؑؓ\uFDFD\uFDFA:’[]{}"


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
    "split_non_empty_lines",
    "contains_non_urdu_characters",
    "get_last_token",
    "strip_suffix_phrase",
    "TRAILING_STRIP_CHARS",
]

