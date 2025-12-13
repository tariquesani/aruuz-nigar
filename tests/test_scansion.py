"""
Tests for scansion engine.

Tests word code assignment methods with known words.
"""

import unittest
from aruuz.scansion import (
    length_one_scan,
    length_two_scan,
    length_three_scan,
    length_four_scan,
    length_five_scan,
    assign_code,
    is_vowel_plus_h,
    is_muarrab,
    locate_araab,
    contains_noon
)
from aruuz.models import Words, Lines


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions."""

    def test_is_vowel_plus_h(self):
        """Test is_vowel_plus_h function."""
        self.assertTrue(is_vowel_plus_h('ا'))
        self.assertTrue(is_vowel_plus_h('ی'))
        self.assertTrue(is_vowel_plus_h('ے'))
        self.assertTrue(is_vowel_plus_h('و'))
        self.assertTrue(is_vowel_plus_h('ہ'))
        self.assertTrue(is_vowel_plus_h('ؤ'))
        self.assertFalse(is_vowel_plus_h('ب'))
        self.assertFalse(is_vowel_plus_h('ک'))

    def test_is_muarrab(self):
        """Test is_muarrab function."""
        # Word with diacritics
        self.assertTrue(is_muarrab("کتاب\u064E"))  # with zabar
        self.assertTrue(is_muarrab("کتاب\u0650"))  # with zer
        # Word without diacritics
        self.assertFalse(is_muarrab("کتاب"))
        self.assertFalse(is_muarrab(""))

    def test_locate_araab(self):
        """Test locate_araab function."""
        # Word with diacritics
        result = locate_araab("ک\u064Eتاب")
        self.assertIsInstance(result, str)
        # Word without diacritics
        result = locate_araab("کتاب")
        self.assertIsInstance(result, str)

    def test_contains_noon(self):
        """Test contains_noon function."""
        self.assertTrue(contains_noon("نظر"))
        self.assertTrue(contains_noon("انگ"))
        self.assertFalse(contains_noon("کتاب"))
        self.assertFalse(contains_noon("ک"))


class TestLengthOneScan(unittest.TestCase):
    """Test length_one_scan method."""

    def test_alif_madd(self):
        """Test آ (alif madd) returns long syllable."""
        result = length_one_scan("آ")
        self.assertEqual(result, "=")

    def test_other_characters(self):
        """Test other single characters return short syllable."""
        result = length_one_scan("ک")
        self.assertEqual(result, "-")
        result = length_one_scan("ب")
        self.assertEqual(result, "-")


class TestLengthTwoScan(unittest.TestCase):
    """Test length_two_scan method."""

    def test_starts_with_alif_madd(self):
        """Test words starting with آ return =-."""
        result = length_two_scan("آب")
        self.assertEqual(result, "=-")

    def test_ends_with_vowel_h(self):
        """Test words ending with vowel+h return x (flexible)."""
        # Words ending in ا،ی،ے،و،ہ should be flexible
        result = length_two_scan("کا")  # ends with ا
        self.assertEqual(result, "x")
        result = length_two_scan("کی")  # ends with ی
        self.assertEqual(result, "x")

    def test_default_case(self):
        """Test default case returns =."""
        result = length_two_scan("کب")
        self.assertEqual(result, "=")


class TestLengthThreeScan(unittest.TestCase):
    """Test length_three_scan method."""

    def test_single_character_after_removal(self):
        """Test when stripped length is 1."""
        # Word that becomes single char after removing diacritics
        result = length_three_scan("آ\u0652")  # آ with jazm
        self.assertIn(result, ["-", "="])

    def test_two_character_after_removal(self):
        """Test when stripped length is 2, delegates to length_two_scan."""
        result = length_three_scan("آب")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_starts_with_alif_madd(self):
        """Test words starting with آ."""
        result = length_three_scan("آنا")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_alif_at_center(self):
        """Test words with alif at center."""
        result = length_three_scan("کتاب")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_vowel_at_end(self):
        """Test words with vowel at end."""
        result = length_three_scan("کسی")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestLengthFourScan(unittest.TestCase):
    """Test length_four_scan method."""

    def test_delegates_to_shorter_methods(self):
        """Test that it delegates to shorter scan methods when appropriate."""
        # Should delegate to length_one_scan, length_two_scan, or length_three_scan
        result = length_four_scan("آ")
        self.assertIsInstance(result, str)

    def test_starts_with_alif_madd(self):
        """Test words starting with آ."""
        result = length_four_scan("آناں")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_alif_at_position_2(self):
        """Test words with alif at position 2."""
        result = length_four_scan("کتاب")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestLengthFiveScan(unittest.TestCase):
    """Test length_five_scan method."""

    def test_delegates_to_shorter_methods(self):
        """Test that it delegates to shorter scan methods when appropriate."""
        result = length_five_scan("کتاب")
        self.assertIsInstance(result, str)

    def test_starts_with_alif_madd(self):
        """Test words starting with آ."""
        result = length_five_scan("آناں")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_longer_words(self):
        """Test longer words."""
        result = length_five_scan("کتابیں")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestAssignCode(unittest.TestCase):
    """Test assign_code method."""

    def test_single_character_word(self):
        """Test assigning code to single character word."""
        word = Words()
        word.word = "آ"
        word.taqti = []
        result = assign_code(word)
        self.assertEqual(result, "=")

    def test_two_character_word(self):
        """Test assigning code to two character word."""
        word = Words()
        word.word = "آب"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_three_character_word(self):
        """Test assigning code to three character word."""
        word = Words()
        word.word = "کتاب"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_with_taqti(self):
        """Test assigning code when taqti is available."""
        word = Words()
        word.word = "کتاب"
        word.taqti = ["کتاب"]  # Simple taqti
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_with_taqti_multiple_syllables(self):
        """Test assigning code with taqti containing multiple syllables."""
        word = Words()
        word.word = "کتابیں"
        word.taqti = ["کتاب + یں"]  # Multiple syllables
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_word_end_flexible_syllable(self):
        """Test word-end flexible syllable handling."""
        word = Words()
        word.word = "کسی"
        word.taqti = ["کسی"]
        word.language = []
        word.modified = False
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_arabic_word_ending(self):
        """Test Arabic word ending rules."""
        word = Words()
        word.word = "کتاب"
        word.taqti = ["کتاب"]
        word.language = ["عربی"]
        word.modified = False
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_persian_word_ending(self):
        """Test Persian word ending rules."""
        word = Words()
        word.word = "کتابا"
        word.taqti = ["کتابا"]
        word.language = ["فارسی"]
        word.modified = False
        result = assign_code(word)
        self.assertIsInstance(result, str)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_word(self):
        """Test handling of empty word."""
        word = Words()
        word.word = ""
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_word_with_special_characters(self):
        """Test words with ھ and ں characters."""
        word = Words()
        word.word = "کتابھ"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_word_with_diacritics(self):
        """Test words with diacritical marks."""
        word = Words()
        word.word = "کتاب\u064E"  # with zabar
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)


class TestLinesParsing(unittest.TestCase):
    """Test Lines class line parsing functionality."""

    def test_basic_line_parsing(self):
        """Test parsing a simple line into words."""
        line = Lines("کتاب و قلم")
        self.assertEqual(len(line.words_list), 3)
        self.assertEqual(line.words_list[0].word, "کتاب")
        self.assertEqual(line.words_list[1].word, "و")
        self.assertEqual(line.words_list[2].word, "قلم")

    def test_line_with_punctuation(self):
        """Test that punctuation is removed from lines."""
        line = Lines("کتاب، قلم! شعر؟")
        # Punctuation should be removed, so we should get clean words
        self.assertGreater(len(line.words_list), 0)
        # Check that punctuation is not in words
        for word in line.words_list:
            self.assertNotIn(",", word.word)
            self.assertNotIn("!", word.word)
            self.assertNotIn("؟", word.word)

    def test_line_with_comma_delimiter(self):
        """Test splitting by comma delimiter."""
        line = Lines("کتاب،قلم،شعر")
        self.assertEqual(len(line.words_list), 3)
        self.assertEqual(line.words_list[0].word, "کتاب")
        self.assertEqual(line.words_list[1].word, "قلم")
        self.assertEqual(line.words_list[2].word, "شعر")

    def test_line_with_multiple_spaces(self):
        """Test handling of multiple spaces."""
        line = Lines("کتاب    قلم     شعر")
        # Multiple spaces should be treated as single delimiter
        self.assertEqual(len(line.words_list), 3)

    def test_word_cleaning_applied(self):
        """Test that clean_word transformations are applied."""
        # Test ئ -> یٔ replacement
        line = Lines("کتابئ")
        self.assertEqual(len(line.words_list), 1)
        self.assertEqual(line.words_list[0].word, "کتابیٔ")

    def test_word_length_calculation(self):
        """Test that word length is calculated after removing diacritics."""
        line = Lines("کتاب")
        self.assertEqual(len(line.words_list), 1)
        # Length should be calculated after removing diacritics
        word = line.words_list[0]
        self.assertGreater(word.length, 0)
        # Length should match the word without diacritics
        from aruuz.utils.araab import remove_araab
        expected_length = len(remove_araab(word.word))
        self.assertEqual(word.length, expected_length)

    def test_empty_line(self):
        """Test handling of empty line."""
        line = Lines("")
        self.assertEqual(len(line.words_list), 0)
        self.assertEqual(line.original_line, "")

    def test_line_with_only_punctuation(self):
        """Test line with only punctuation."""
        line = Lines("،!؟")
        # Should result in no words
        self.assertEqual(len(line.words_list), 0)

    def test_original_line_stored(self):
        """Test that original (cleaned) line is stored."""
        line = Lines("کتاب، قلم")
        # Original line should be cleaned (punctuation removed)
        self.assertIn("کتاب", line.original_line)
        self.assertIn("قلم", line.original_line)
        # But comma should be removed
        self.assertNotIn("،", line.original_line)

    def test_word_with_alif_madd(self):
        """Test that ا + madd is converted to آ."""
        # This tests clean_word functionality through Lines
        line = Lines("ا\u0653ب")  # ا + madd
        self.assertEqual(len(line.words_list), 1)
        self.assertEqual(line.words_list[0].word, "آب")

    def test_word_with_heh_goal(self):
        """Test that \u06C2 is converted to \u06C1\u0654."""
        line = Lines("ک\u06C2اں")
        self.assertEqual(len(line.words_list), 1)
        self.assertEqual(line.words_list[0].word, "ک\u06C1\u0654اں")


if __name__ == '__main__':
    unittest.main()
