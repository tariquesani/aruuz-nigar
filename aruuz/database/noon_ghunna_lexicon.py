"""
Ghunna flags for the noon keep/drop model.

The keep/drop model defaults to keeping a noon and only drops it on positive
evidence. For words whose ghunna cannot be read off the spelling — چاند is not
spelled any differently from بند — that evidence has to come from a lexicon.

Two sources are consulted, in order:

1. a ``noon_ghunna`` table in the scansion database, if the deployment has one.
   Expected columns are ``word`` and ``decision``; ``decision`` is one of
   ``drop``, ``either`` or ``keep``. This is the source meant to grow.
2. ``noon_ghunna_flags.json`` shipped beside the database, a small seed for the
   words the engine has to get right out of the box.

Entries are stems rather than inflected forms. When the flagged noon sits in a
nasal+stop cluster, suffixation cannot change it, so a flag on جھانک also
answers for جھانکتے، جھانکتی and جھانکنا. That is what keeps this from turning
into a list of every noon-bearing word in the language, which would not scale.
"""

import json
import logging
import os
import sqlite3
from typing import Dict, Optional, Tuple

from aruuz.database.config import get_db_path
from aruuz.utils.araab import remove_araab

logger = logging.getLogger(__name__)

FLAGS_FILENAME = "noon_ghunna_flags.json"
TABLE_NAME = "noon_ghunna"

# Stop consonants: ک، گ، ت، د، پ، ب، چ، ج
STOP_CONSONANTS = "کگتدپبچج"

# Shortest stem allowed to answer for longer words. Two-letter stems match far
# too much to be safe.
MIN_STEM_LENGTH = 3

_VALID_DECISIONS = ("drop", "either", "keep")


class NoonGhunnaLexicon:
    """
    Per-word ghunna flags, loaded once and cached.

    Attributes:
        entries: Mapping of araab-stripped word to decision.
    """

    def __init__(self, db_path: Optional[str] = None, flags_path: Optional[str] = None):
        """
        Load the flags from the database table and the JSON seed.

        Args:
            db_path: Optional path to the scansion database. Falls back to
                `config.get_db_path()`, and a missing database is not an error.
            flags_path: Optional path to the JSON seed file.
        """
        self.entries: Dict[str, str] = {}
        self._load_seed(flags_path)
        self._load_table(db_path)
        self._reindex_stems()

    @classmethod
    def from_entries(cls, entries: Dict[str, str]) -> "NoonGhunnaLexicon":
        """
        Build a lexicon from an explicit mapping, reading neither file nor database.

        Args:
            entries: Mapping of word to decision. Unknown decisions are dropped.

        Returns:
            A NoonGhunnaLexicon holding only these flags.
        """
        lexicon = cls.__new__(cls)
        lexicon.entries = {}
        for word, decision in entries.items():
            lexicon._add(word, decision, "explicit")
        lexicon._reindex_stems()
        return lexicon

    def _reindex_stems(self) -> None:
        """Cache the entries that may answer for longer words, longest first."""
        self._stems = tuple(
            sorted(
                (w for w in self.entries if self._is_inheritable_stem(w)),
                key=len,
                reverse=True,
            )
        )

    def decision_for(self, word: str) -> Optional[Tuple[str, str]]:
        """
        Look up the ghunna flag for a word.

        An exact match wins. Failing that, the longest inheritable stem that the
        word is built on answers for it.

        Args:
            word: Word to look up; diacritics are ignored.

        Returns:
            ``(decision, matched_entry)``, or None when nothing is flagged.
        """
        stripped = remove_araab(word)
        if not stripped:
            return None

        decision = self.entries.get(stripped)
        if decision is not None:
            return decision, stripped

        for stem in self._stems:
            if len(stem) < len(stripped) and stripped.startswith(stem):
                return self.entries[stem], stem

        return None

    @staticmethod
    def _is_inheritable_stem(entry: str) -> bool:
        """
        Check whether a flag may be inherited by words built on this entry.

        Only stems whose noon sits in a nasal+stop cluster qualify. A suffix
        cannot break that cluster up, so the ghunna reading survives into the
        derived form — جھانک into جھانکتے. A stem like جان has no cluster, so it
        answers only for itself and leaves جانب alone.

        Args:
            entry: Araab-stripped lexicon key.

        Returns:
            True if the entry may answer for longer words.
        """
        if len(entry) < MIN_STEM_LENGTH:
            return False
        return any(
            entry[i] == "ن" and entry[i + 1] in STOP_CONSONANTS
            for i in range(len(entry) - 1)
        )

    def _add(self, word: Optional[str], decision: Optional[str], source: str) -> None:
        """Record one flag, ignoring malformed rows."""
        if not word or not decision:
            return
        decision = decision.strip().lower()
        if decision not in _VALID_DECISIONS:
            logger.debug("Ignoring %s ghunna flag for '%s': unknown decision '%s'", source, word, decision)
            return
        self.entries[remove_araab(word.strip())] = decision

    def _load_seed(self, flags_path: Optional[str]) -> None:
        """Load the JSON seed shipped with the package."""
        if flags_path is None:
            flags_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), FLAGS_FILENAME)
        if not os.path.exists(flags_path):
            return
        try:
            with open(flags_path, encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, ValueError) as exc:
            logger.warning("Could not read noon ghunna seed '%s': %s", flags_path, exc)
            return
        for entry in payload.get("entries", []):
            self._add(entry.get("word"), entry.get("decision"), "seed")

    def _load_table(self, db_path: Optional[str]) -> None:
        """Load the optional `noon_ghunna` database table, if it exists."""
        try:
            path = db_path if db_path is not None else get_db_path()
        except FileNotFoundError:
            return
        try:
            conn = sqlite3.connect(path)
        except sqlite3.Error as exc:
            logger.debug("Could not open database for ghunna flags: %s", exc)
            return
        try:
            exists = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (TABLE_NAME,)
            ).fetchone()
            if not exists:
                return
            for word, decision in conn.execute(f"SELECT word, decision FROM {TABLE_NAME}"):
                self._add(word, decision, "database")
        except sqlite3.Error as exc:
            logger.warning("Could not read '%s' table: %s", TABLE_NAME, exc)
        finally:
            conn.close()


_default_lexicon: Optional[NoonGhunnaLexicon] = None


def get_noon_ghunna_lexicon() -> NoonGhunnaLexicon:
    """
    Get the shared lexicon, building it on first use.

    Returns:
        The process-wide NoonGhunnaLexicon.
    """
    global _default_lexicon
    if _default_lexicon is None:
        _default_lexicon = NoonGhunnaLexicon()
    return _default_lexicon


__all__ = ["NoonGhunnaLexicon", "get_noon_ghunna_lexicon"]
