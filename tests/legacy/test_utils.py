"""
Tests for utility functions.
"""

import unittest

from aruuz.utils.araab import remove_araab
from aruuz.utils.text import clean_word, clean_line


class TestAraabUtils(unittest.TestCase):
    def test_remove_araab_removes_known_marks(self):
        # Arabic diacritics: shadd (\u0651), zabar (\u064E), paish (\u064F)
        word = "کَتّابٌ"  # contains zabar, shadd, paish
        expected = "کتاب"
        self.assertEqual(remove_araab(word), expected)

    def test_remove_araab_empty_and_none(self):
        self.assertEqual(remove_araab(""), "")
        self.assertEqual(remove_araab(None), "")

    def test_remove_araab_no_diacritics(self):
        word = "کتاب"
        self.assertEqual(remove_araab(word), word)


class TestTextUtils(unittest.TestCase):
    def test_clean_word_final_hamza_yeh(self):
        self.assertEqual(clean_word("شیئ"), "شییٔ")
        self.assertEqual(clean_word("کتابئ"), "کتابیٔ")

    def test_clean_word_alef_madd_and_heh_goal(self):
        self.assertEqual(clean_word("\u0627\u0653ب"), "آب")  # ا + madd
        self.assertEqual(clean_word("وہ\u06C2"), "وہ\u06C1\u0654")

    def test_clean_word_empty_and_none(self):
        self.assertEqual(clean_word(""), "")
        self.assertEqual(clean_word(None), "")

    def test_clean_line_removes_punctuation_and_zero_width(self):
        line = "،ؔ؟ؑؓ*\"کتاب\u200B \u200C!\u200D؎:;"
        self.assertEqual(clean_line(line), "کتاب ")

    def test_clean_line_no_op_when_clean(self):
        line = "کتاب و قلم"
        self.assertEqual(clean_line(line), line)


if __name__ == "__main__":
    unittest.main()