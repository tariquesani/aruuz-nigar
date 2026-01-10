"""
Tests for utility functions.
"""

import unittest

from aruuz.utils.araab import remove_araab
from aruuz.utils.text import clean_word, clean_line, handle_noon_followed_by_stop


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

    def test_handle_noon_followed_by_stop_example_case(self):
        """Test the example case: جھانکتے -> جھانک, تے"""
        words = ["جھانکتے"]
        expected = ["جھانک", "تے"]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_all_consonants(self):
        """Test all stop consonants: ک، گ، ت، د، پ، ب، چ، ج"""
        test_cases = [
            (["جھانکتے"], ["جھانک", "تے"]),  # ک
            (["testنگس"], ["testنگ", "س"]),  # گ
            (["testنتس"], ["testنت", "س"]),  # ت
            (["testندس"], ["testند", "س"]),  # د
            (["testنپس"], ["testنپ", "س"]),  # پ
            (["testنبس"], ["testنب", "س"]),  # ب
            (["testنچس"], ["testنچ", "س"]),  # چ
            (["testنجس"], ["testنج", "س"]),  # ج
        ]
        for words, expected in test_cases:
            with self.subTest(words=words):
                self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_no_match(self):
        """Test words that don't match the pattern remain unchanged"""
        words = ["کتاب", "قلم", "درخت"]
        expected = ["کتاب", "قلم", "درخت"]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_empty_list(self):
        """Test empty list input"""
        self.assertEqual(handle_noon_followed_by_stop([]), [])

    def test_handle_noon_followed_by_stop_empty_strings(self):
        """Test empty strings in list"""
        words = ["", "جھانکتے", ""]
        expected = ["", "جھانک", "تے", ""]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_mixed_words(self):
        """Test list with both matching and non-matching words"""
        words = ["کتاب", "جھانکتے", "قلم", "دیکھتے"]
        expected = ["کتاب", "جھانک", "تے", "قلم", "دیکھتے"]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_preserves_order(self):
        """Test that word order is preserved"""
        words = ["کتاب", "جھانکتے", "درخت", "جھانکتے"]
        expected = ["کتاب", "جھانک", "تے", "درخت", "جھانک", "تے"]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_noon_not_followed_by_stop(self):
        """Test noon that is not followed by a stop consonant"""
        words = ["جھاں"]  # noon not followed by stop consonant
        expected = ["جھاں"]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)

    def test_handle_noon_followed_by_stop_stop_without_suffix(self):
        """Test noon followed by stop consonant but no remaining suffix"""
        # Word ending with noon+stop (no suffix after)
        words = ["جھانک"]  # ends with ک but no noon before it
        expected = ["جھانک"]
        self.assertEqual(handle_noon_followed_by_stop(words), expected)
        
        # Word with noon+stop at end
        words2 = ["testنک"]
        expected2 = ["testنک"]
        self.assertEqual(handle_noon_followed_by_stop(words2), expected2)


if __name__ == "__main__":
    unittest.main()