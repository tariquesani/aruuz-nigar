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
PHONETIC_MAP: dict[str, str] = {
    "ث": "س",
    "ص": "س",
    "ذ": "ز",
    "ض": "ز",
    "ظ": "ز",
    "ح": "ہ",
    "ط": "ت",
}

# Long vowels used to anchor kafiya suffix extraction.
VOWELS: set[str] = {"ا", "ی", "ے", "و"}

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


def phonetic_normalize(word: str) -> str:
    """
    Apply the Urdu homophone map to a word.
    """
    return "".join(PHONETIC_MAP.get(c, c) for c in word)


def full_normalize(word: str) -> str:
    """
    Full pipeline for kafiya matching: script normalization then phonetic map.
    """
    return phonetic_normalize(normalize_urdu_text(word))


def exact_suffix_length(word: str) -> int:
    """
    Return suffix length from the last long vowel to the end.
    Falls back to up to 2 chars when no long vowel is found.
    """
    for i in range(len(word) - 1, -1, -1):
        if word[i] in VOWELS:
            return len(word) - i
    return min(2, len(word))


def extract_kafiya_unit(word: str) -> str:
    """
    Return kafiya unit anchored at the last long vowel.
    Falls back to final consonant class when no long vowel is present.
    """
    if not word:
        return ""
    suffix_len = exact_suffix_length(word)
    return word[-suffix_len:] if suffix_len > 0 else ""


def extract_onset(word: str) -> str | None:
    """
    Return the consonant immediately before the last long vowel.
    """
    for i in range(len(word) - 1, -1, -1):
        if word[i] in VOWELS:
            return word[i - 1] if i > 0 else None
    return None


def extract_final_consonant_class(word: str) -> str:
    """
    Return final consonant class key used for implicit short-vowel rhyme fallback.
    """
    return word[-1] if word else ""


def extract_kafiya_key(word: str, mode: str) -> str:
    """
    Extract comparable key for the given mode.
    """
    if mode == "explicit_unit":
        return extract_kafiya_unit(word)
    if mode == "implicit_final_class":
        return extract_final_consonant_class(word)
    return ""


def resolve_kafiya_reference(query_word: str, matla_word: str) -> tuple[str, str]:
    """
    Resolve reference mode and key from matla pair.
    Modes:
      - explicit_unit: both share same explicit/anchored unit
      - implicit_final_class: fallback on final consonant class
      - no_match: no shared reference
    """
    q_unit = extract_kafiya_unit(query_word)
    m_unit = extract_kafiya_unit(matla_word)
    if q_unit and q_unit == m_unit:
        return "explicit_unit", q_unit

    q_class = extract_final_consonant_class(query_word)
    m_class = extract_final_consonant_class(matla_word)
    if q_class and q_class == m_class:
        return "implicit_final_class", q_class

    return "no_match", ""


def is_kafiya_match(reference_key: str, mode: str, candidate_word: str) -> bool:
    """
    Check whether candidate matches the resolved reference key under mode.
    """
    if not reference_key:
        return False
    return extract_kafiya_key(candidate_word, mode) == reference_key


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
    "exact_suffix_length",
    "extract_kafiya_unit",
    "extract_onset",
    "extract_final_consonant_class",
    "extract_kafiya_key",
    "resolve_kafiya_reference",
    "is_kafiya_match",
    "split_non_empty_lines",
    "contains_non_urdu_characters",
    "get_last_token",
    "strip_suffix_phrase",
    "CHAR_MAP",
    "PHONETIC_MAP",
    "VOWELS",
    "TRAILING_STRIP_CHARS",
]

