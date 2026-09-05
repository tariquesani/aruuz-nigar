"""
Keep/Drop Model for Medial Noon (نون)

Classical taqṭīʿ treats a noon inside a word as one of three cases, and it
decides between them on the single word:

- **نونِ غنہ** (nasalisation) — the noon is not a consonant of its own. It carries
  no weight, so it is dropped and the word is recounted without it (چاند → چاد).
- **نونِ اصلی** (real noon) — an ordinary consonant, counted like any other letter.
- **نونِ شبہِ غنہ** (weak, but still counted, e.g. جنگ) — kept.

None of these is a word split. A token boundary in this engine is a *word*
boundary, and the prosodic rules that run later (Al, izafat, ataf, grafting,
final-vowel weakening) all assume that. Splitting جھانکتے into جھانک + تے to make
the length scanners happy invented a boundary that does not exist and let those
rules fire in the middle of a word.

Because a wrongly dropped noon silently shortens a line, the default is KEEP.
A noon is dropped only when there is positive evidence of ghunna:

1. the nasal is written ں (the noon ghunna letter),
2. the noon is explicitly marked with jazm and matches one of the patterns in
   :func:`aruuz.scansion.length_scanners.noon_ghunna`, which adjusts the code
   rather than the spelling,
3. the ghunna lexicon flags that word — see
   :class:`aruuz.database.noon_ghunna_lexicon.NoonGhunnaLexicon`.

A word that can legitimately be read either way depending on the meter (جان as
against جاں) is flagged ``either`` in the lexicon and gets both scansions;
bahr matching then picks whichever fits.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional

from aruuz.utils.araab import ARABIC_DIACRITICS, remove_araab

if TYPE_CHECKING:
    from aruuz.database.noon_ghunna_lexicon import NoonGhunnaLexicon

NOON = "\u0646"  # ن
NOON_GHUNNA = "\u06BA"  # ں
JAZM = ARABIC_DIACRITICS[2]  # \u0652

# Decisions the model can reach for a given noon.
KEEP = "keep"
DROP = "drop"
EITHER = "either"

_VALID_DECISIONS = (KEEP, DROP, EITHER)


@dataclass(frozen=True)
class NoonDecision:
    """
    Outcome of the keep/drop question for one word.

    Attributes:
        decision: One of KEEP, DROP, EITHER.
        index: Position of the noon in the araab-stripped word, or -1 when the
            word has no candidate noon.
        reason: Short machine-readable tag naming the evidence that was used.
    """

    decision: str
    index: int = -1
    reason: str = "default_keep"

    @property
    def keeps_noon(self) -> bool:
        """True when no drop-variant scansion should be generated."""
        return self.decision == KEEP or self.index < 0


def is_protected_noon(stripped: str, index: int) -> bool:
    """
    Check whether a noon must be counted whatever other evidence says.

    Two positions are protected:

    - A word-initial noon (نمک، نکما) is a syllable onset, never ghunna.
    - The prefix ان- (انتخاب، انتقام، انتقال، اندرون) is always pronounced and
      always counted. This guard used to live in the token-splitting
      preprocessor; it belongs to the keep/drop decision instead.

    Args:
        stripped: Word with diacritics already removed.
        index: Position of the noon within `stripped`.

    Returns:
        True if the noon at `index` may never be treated as ghunna.
    """
    if index <= 0:
        return True
    if index == 1 and stripped.startswith("ا" + NOON):
        return True
    return False


def medial_noon_positions(stripped: str) -> List[int]:
    """
    Find the positions of every noon that could carry ghunna on its own.

    A word-final noon is excluded because the orthography already distinguishes
    it: a final nasalised noon is written ں, which the scanners drop, while a
    final ن is a real consonant.

    Args:
        stripped: Word with diacritics already removed.

    Returns:
        Ascending list of positions within `stripped`.
    """
    return [
        i
        for i in range(1, max(len(stripped) - 1, 0))
        if stripped[i] == NOON and not is_protected_noon(stripped, i)
    ]


def candidate_noon_positions(stripped: str) -> List[int]:
    """
    Find every noon the lexicon is allowed to speak about.

    This is :func:`medial_noon_positions` plus a word-final noon, which the
    model never drops by itself but which the lexicon can flag — that is what
    makes the جان / جاں pair scannable both ways.

    Args:
        stripped: Word with diacritics already removed.

    Returns:
        Ascending list of positions within `stripped`.
    """
    positions = medial_noon_positions(stripped)
    last = len(stripped) - 1
    if last > 0 and stripped[last] == NOON and not is_protected_noon(stripped, last):
        positions.append(last)
    return positions


def has_jazm(word: str, index: int) -> bool:
    """
    Check whether the letter at `index` carries an explicit jazm (سکون).

    Args:
        word: Word which may still contain diacritics.
        index: Position counted over letters, ignoring diacritics.

    Returns:
        True if a jazm is written on that letter.
    """
    letter_index = -1
    for i, char in enumerate(word):
        if char in ARABIC_DIACRITICS:
            continue
        letter_index += 1
        if letter_index == index:
            return i + 1 < len(word) and word[i + 1] == JAZM
    return False


def drop_noon(word: str, index: int) -> str:
    """
    Remove one noon from a word, keeping the spelling of everything else.

    The index counts letters and ignores diacritics, so چانْد with index 2 gives
    چاد and any diacritic sitting on the dropped noon goes with it. The caller
    keeps the original spelling for display; only the scansion uses this form.

    Args:
        word: Word which may still contain diacritics.
        index: Position of the noon, counted over letters.

    Returns:
        The word without that noon.
    """
    out = []
    letter_index = -1
    for char in word:
        if char in ARABIC_DIACRITICS:
            # Diacritics belong to the letter in front of them.
            if letter_index != index:
                out.append(char)
            continue
        letter_index += 1
        if letter_index != index:
            out.append(char)
    return "".join(out)


def classify_noon(word: str, lexicon: Optional["NoonGhunnaLexicon"] = None) -> NoonDecision:
    """
    Decide whether the noon in a word is kept, dropped, or either.

    Args:
        word: Word as written, diacritics included.
        lexicon: Optional ghunna lexicon. Without one the model still runs, and
            every word falls through to the KEEP default.

    Returns:
        A NoonDecision. KEEP is returned whenever there is no positive evidence
        of ghunna, which is the common case.
    """
    # Positions count letters and ignore diacritics, so they stay valid for
    # drop_noon() against the original spelling.
    stripped = remove_araab(word)
    candidates = candidate_noon_positions(stripped)

    if not candidates:
        # A nasal written ں is ghunna by spelling, and the scanners already
        # strip it before counting. Name it so explanations can say why.
        reason = "written_as_noon_ghunna" if NOON_GHUNNA in stripped else "no_candidate_noon"
        return NoonDecision(KEEP, -1, reason)

    if lexicon is not None:
        flagged = lexicon.decision_for(stripped)
        if flagged is not None:
            decision, entry = flagged
            if decision in _VALID_DECISIONS and decision != KEEP:
                index = _noon_index_for_entry(stripped, entry, candidates)
                if index >= 0:
                    return NoonDecision(decision, index, f"lexicon:{entry}")
            return NoonDecision(KEEP, -1, f"lexicon:{entry}")

    # نونِ اصلی / نونِ شبہِ غنہ. A jazm-marked noon is handled by noon_ghunna()
    # inside the length scanners, which adjusts the code instead of the
    # spelling, so there is nothing to drop here.
    return NoonDecision(KEEP, -1, "default_keep")


def _noon_index_for_entry(stripped: str, entry: str, candidates: List[int]) -> int:
    """
    Pick which noon a lexicon entry is talking about.

    Args:
        stripped: The word being scanned, diacritics removed.
        entry: The lexicon key that matched, either the word itself or a stem.
        candidates: Positions returned by :func:`candidate_noon_positions`.

    Returns:
        Position of the flagged noon, or -1 if the entry does not identify one.
    """
    entry_length = len(remove_araab(entry))
    within_entry = [i for i in candidates if i < entry_length]
    return within_entry[-1] if within_entry else -1


__all__ = [
    "KEEP",
    "DROP",
    "EITHER",
    "NOON",
    "NOON_GHUNNA",
    "NoonDecision",
    "candidate_noon_positions",
    "classify_noon",
    "drop_noon",
    "has_jazm",
    "is_protected_noon",
    "medial_noon_positions",
]
