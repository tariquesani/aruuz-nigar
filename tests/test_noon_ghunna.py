"""
Tests for the noon keep/drop model.

These replace the tests that asserted the old nasal-coda word split
(جھانکتے -> جھانک + تے). A word is never split at a nasal+stop cluster any more;
the engine decides on the single word whether its noon is نونِ غنہ (dropped and
recounted), نونِ اصلی or نونِ شبہِ غنہ (kept).
"""

import unittest

from aruuz.database.noon_ghunna_lexicon import NoonGhunnaLexicon, get_noon_ghunna_lexicon
from aruuz.database.word_lookup import WordLookup
from aruuz.models import Lines, Words
from aruuz.scansion.length_scanners import noon_ghunna
from aruuz.scansion.noon_model import (
    DROP,
    EITHER,
    KEEP,
    candidate_noon_positions,
    classify_noon,
    drop_noon,
    has_jazm,
    is_protected_noon,
    medial_noon_positions,
)

JAZM = "\u0652"

# Words whose noon must always be counted: the ان- prefix named in the issue,
# plus the nasal+stop clusters that the old splitter also used to break up.
ALWAYS_KEPT = ["انتخاب", "انتقام", "انتقال", "اندرون", "اندر", "انگ", "جنگ", "رنگ", "بند"]


class TestNoTokenSplitting(unittest.TestCase):
    """A word is one token, whatever nasal clusters it contains."""

    def test_nasal_stop_word_is_a_single_token(self):
        # legacy: this used to tokenise as ["جھانک", "تے"].
        self.assertEqual([w.word for w in Lines("جھانکتے").words_list], ["جھانکتے"])

    def test_an_prefix_words_are_never_split(self):
        # legacy: انتخاب used to tokenise as ["انت", "خاب"].
        for word in ["انتخاب", "انتقام", "انتقال", "اندرون"]:
            with self.subTest(word=word):
                self.assertEqual([w.word for w in Lines(word).words_list], [word])

    def test_line_token_count_matches_word_count(self):
        line = Lines("چاندنی رات میں جھانکتے ہوئے")
        self.assertEqual(
            [w.word for w in line.words_list],
            ["چاندنی", "رات", "میں", "جھانکتے", "ہوئے"],
        )

    def test_original_spelling_is_preserved(self):
        """Dropping the noon changes the scansion, never the stored word."""
        word = _scan("جھانکتے")
        self.assertEqual(word.word, "جھانکتے")


class TestProtectedNoon(unittest.TestCase):
    """Word-initial noon and the ان- prefix are نونِ اصلی."""

    def test_word_initial_noon_is_protected(self):
        self.assertTrue(is_protected_noon("نمک", 0))
        self.assertTrue(is_protected_noon("نکما", 0))

    def test_an_prefix_noon_is_protected(self):
        for word in ["انتخاب", "انتقام", "انتقال", "اندرون", "اندر", "انگ"]:
            with self.subTest(word=word):
                self.assertTrue(is_protected_noon(word, 1))

    def test_other_medial_noon_is_not_protected(self):
        self.assertFalse(is_protected_noon("چاند", 2))
        self.assertFalse(is_protected_noon("جھانکتے", 3))

    def test_protected_noon_is_never_a_candidate(self):
        for word in ["انتخاب", "انتقام", "انتقال", "اندر", "انگ", "نمک"]:
            with self.subTest(word=word):
                self.assertEqual(medial_noon_positions(word), [])

    def test_an_prefix_words_always_keep_their_noon(self):
        for word in ["انتخاب", "انتقام", "انتقال", "اندرون"]:
            with self.subTest(word=word):
                self.assertEqual(classify_noon(word, get_noon_ghunna_lexicon()).decision, KEEP)


class TestNoonPositions(unittest.TestCase):
    def test_medial_noon_found(self):
        self.assertEqual(medial_noon_positions("چاند"), [2])
        self.assertEqual(medial_noon_positions("جھانکتے"), [3])

    def test_final_noon_is_not_a_default_candidate(self):
        self.assertEqual(medial_noon_positions("جان"), [])

    def test_final_noon_is_a_lexicon_candidate(self):
        self.assertEqual(candidate_noon_positions("جان"), [2])

    def test_no_noon_at_all(self):
        self.assertEqual(medial_noon_positions("کتاب"), [])
        self.assertEqual(candidate_noon_positions("کتاب"), [])

    def test_empty_word(self):
        self.assertEqual(medial_noon_positions(""), [])
        self.assertEqual(candidate_noon_positions(""), [])


class TestDropNoon(unittest.TestCase):
    def test_drop_plain_noon(self):
        self.assertEqual(drop_noon("چاند", 2), "چاد")
        self.assertEqual(drop_noon("جھانکتے", 3), "جھاکتے")
        self.assertEqual(drop_noon("جان", 2), "جا")

    def test_drop_takes_the_diacritic_with_it(self):
        self.assertEqual(drop_noon("چان" + JAZM + "د", 2), "چاد")

    def test_other_diacritics_survive(self):
        self.assertEqual(drop_noon("جَنْگ", 1), "جَگ")

    def test_index_out_of_range_is_a_no_op(self):
        self.assertEqual(drop_noon("چاند", 9), "چاند")


class TestHasJazm(unittest.TestCase):
    def test_jazm_detected_on_noon(self):
        self.assertTrue(has_jazm("چان" + JAZM + "د", 2))

    def test_no_jazm(self):
        self.assertFalse(has_jazm("چاند", 2))

    def test_index_past_end(self):
        self.assertFalse(has_jazm("چاند", 9))


class TestGhunnaLexicon(unittest.TestCase):
    def setUp(self):
        self.lexicon = NoonGhunnaLexicon.from_entries(
            {"جھانک": DROP, "چاند": DROP, "جان": EITHER, "چاندپن": KEEP}
        )

    def test_exact_match(self):
        self.assertEqual(self.lexicon.decision_for("چاند"), (DROP, "چاند"))

    def test_diacritics_ignored(self):
        self.assertEqual(self.lexicon.decision_for("چانْد"), (DROP, "چاند"))

    def test_stem_answers_for_inflected_forms(self):
        for word in ["جھانکتے", "جھانکتی", "جھانکنا", "جھانکوں"]:
            with self.subTest(word=word):
                self.assertEqual(self.lexicon.decision_for(word), (DROP, "جھانک"))

    def test_exact_entry_overrides_stem(self):
        self.assertEqual(self.lexicon.decision_for("چاندپن"), (KEEP, "چاندپن"))

    def test_stem_without_nasal_stop_cluster_does_not_spread(self):
        """جان must not answer for جانب, whose noon is نونِ اصلی."""
        self.assertIsNone(self.lexicon.decision_for("جانب"))
        self.assertIsNone(self.lexicon.decision_for("جانور"))

    def test_unflagged_word(self):
        self.assertIsNone(self.lexicon.decision_for("جنگ"))
        self.assertIsNone(self.lexicon.decision_for(""))

    def test_inheritable_stem_predicate(self):
        self.assertTrue(NoonGhunnaLexicon._is_inheritable_stem("جھانک"))
        self.assertTrue(NoonGhunnaLexicon._is_inheritable_stem("چاند"))
        self.assertFalse(NoonGhunnaLexicon._is_inheritable_stem("جان"))
        self.assertFalse(NoonGhunnaLexicon._is_inheritable_stem("نک"))

    def test_malformed_entries_are_ignored(self):
        lexicon = NoonGhunnaLexicon.from_entries({"چاند": "nonsense", "جنگ": "", "": DROP})
        self.assertEqual(lexicon.entries, {})

    def test_shipped_seed_loads(self):
        seeded = get_noon_ghunna_lexicon()
        self.assertEqual(seeded.decision_for("جھانکتے"), (DROP, "جھانک"))
        self.assertEqual(seeded.decision_for("جان"), (EITHER, "جان"))


class TestClassifyNoon(unittest.TestCase):
    def setUp(self):
        self.lexicon = get_noon_ghunna_lexicon()

    def test_default_is_keep(self):
        """Nothing is dropped without positive evidence of ghunna."""
        for word in ["جنگ", "رنگ", "بند", "کنول", "جانب"]:
            with self.subTest(word=word):
                self.assertEqual(classify_noon(word, self.lexicon).decision, KEEP)

    def test_lexicon_flag_drops(self):
        decision = classify_noon("جھانکتے", self.lexicon)
        self.assertEqual(decision.decision, DROP)
        self.assertEqual(decision.index, 3)
        self.assertFalse(decision.keeps_noon)

    def test_either_flag_targets_the_final_noon(self):
        decision = classify_noon("جان", self.lexicon)
        self.assertEqual(decision.decision, EITHER)
        self.assertEqual(decision.index, 2)

    def test_word_written_with_noon_ghunna_letter(self):
        decision = classify_noon("جاں", self.lexicon)
        self.assertEqual(decision.decision, KEEP)
        self.assertEqual(decision.reason, "written_as_noon_ghunna")

    def test_no_lexicon_still_works(self):
        self.assertEqual(classify_noon("جھانکتے", None).decision, KEEP)


class TestNoonGhunnaCodeAdjustment(unittest.TestCase):
    """The jazm-marked path: noon_ghunna() adjusts the code, never the tokens."""

    def test_an_prefix_code_is_never_reduced(self):
        self.assertEqual(noon_ghunna("اَنْگ", "=-"), "=-")
        self.assertEqual(noon_ghunna("اَنْدَر", "=="), "==")

    def test_ghunna_reduces_code(self):
        self.assertEqual(noon_ghunna("ہَنْس", "=-"), "=")
        self.assertEqual(noon_ghunna("آنْت", "=--"), "=-")

    def test_unmarked_noon_is_untouched(self):
        self.assertEqual(noon_ghunna("چاند", "=-"), "=-")


class TestKeepDropScansion(unittest.TestCase):
    """End-to-end: the code a word ends up with."""

    def test_ghunna_word_is_recounted_without_its_noon(self):
        # legacy: this used to be scored as two tokens, جھانک (=-) plus تے (=).
        word = _scan("جھانکتے")
        self.assertEqual(word.code, ["=-="])
        self.assertTrue(
            any("DROPPED_NOON_GHUNNA_AND_RECOUNTED" in step for step in word.scansion_generation_steps)
        )

    def test_ghunna_flag_is_inherited_by_inflected_forms(self):
        for word in ["جھانکتا", "جھانکتی", "جھانکنا"]:
            with self.subTest(word=word):
                self.assertEqual(_scan(word).code, ["=-="])

    def test_an_prefix_noon_is_counted(self):
        """انتخاب scans as اِن + تِخاب, four morae with the noon counted."""
        self.assertEqual(_scan("انتخاب").code, ["x-=-"])

    def test_default_keep_words_are_unchanged(self):
        for word in ALWAYS_KEPT:
            with self.subTest(word=word):
                scanned = _scan(word)
                self.assertFalse(
                    any("NOON_GHUNNA" in step for step in scanned.scansion_generation_steps),
                    f"{word} should not have been treated as ghunna",
                )

    def test_either_word_offers_both_readings(self):
        """جان keeps its own scansion and gains the جاں one; the bahr picks."""
        codes = _scan("جان").code
        self.assertIn("=-", codes)
        self.assertEqual(codes[1:], _scan("جا").code)

    def test_word_without_noon_is_untouched(self):
        self.assertEqual(_scan("کتاب").code, _scan("کتاب").code)


def _scan(word_text: str) -> Words:
    """Run one word through the full assigner and return the Words object."""
    from aruuz.scansion.word_scansion_assigner import WordScansionAssigner

    word = Words()
    word.word = word_text
    return WordScansionAssigner(WordLookup()).assign_code_to_word(word)


if __name__ == "__main__":
    unittest.main()
