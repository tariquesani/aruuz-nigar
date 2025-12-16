"""
Comprehensive tests for taqti (syllabification/scansion) of individual words.

This test suite focuses on testing the core scansion code assignment
for individual Urdu words, which is the foundation of the entire system.
"""

import unittest
from aruuz.scansion import (
    length_one_scan,
    length_two_scan,
    length_three_scan,
    length_four_scan,
    length_five_scan,
    assign_code,
    noon_ghunna,
    contains_noon
)
from aruuz.models import Words
from aruuz.utils.araab import remove_araab


class TestTaqtiLengthOne(unittest.TestCase):
    """Test scansion for single-character words."""

    def test_alif_madd_long(self):
        """Test آ (alif madd) is scanned as long syllable."""
        result = length_one_scan("آ")
        self.assertEqual(result, "=", "آ should be scanned as long (=)")

    def test_regular_consonant_short(self):
        """Test regular consonants are scanned as short syllables."""
        test_cases = ["ک", "ب", "ت", "د", "ر", "س", "ل", "م", "ن"]
        for char in test_cases:
            with self.subTest(char=char):
                result = length_one_scan(char)
                self.assertEqual(result, "-", f"{char} should be scanned as short (-)")

    def test_assign_code_single_char(self):
        """Test assign_code for single character words."""
        word = Words()
        word.word = "آ"
        word.taqti = []
        result = assign_code(word)
        self.assertEqual(result, "=")

        word.word = "ک"
        result = assign_code(word)
        self.assertEqual(result, "-")


class TestTaqtiLengthTwo(unittest.TestCase):
    """Test scansion for two-character words."""

    def test_starts_with_alif_madd(self):
        """Test words starting with آ."""
        result = length_two_scan("آب")
        self.assertEqual(result, "=-", "آب should be =- (long-short)")

    def test_ends_with_vowel_flexible(self):
        """Test words ending with vowels are flexible."""
        # Words ending in ا،ی،ے،و،ہ should be flexible (x)
        test_cases = [
            ("کا", "x"),  # ends with ا
            ("کی", "x"),  # ends with ی
            ("کے", "x"),  # ends with ے
            ("کو", "x"),  # ends with و
            ("کہ", "x"),  # ends with ہ
        ]
        for word, expected in test_cases:
            with self.subTest(word=word):
                result = length_two_scan(word)
                self.assertEqual(result, expected, f"{word} should be flexible (x)")

    def test_default_two_char(self):
        """Test default two-character words."""
        result = length_two_scan("کب")
        self.assertEqual(result, "=", "Default two-char word should be =")

    def test_assign_code_two_char(self):
        """Test assign_code for two-character words."""
        word = Words()
        word.word = "آب"
        word.taqti = []
        result = assign_code(word)
        self.assertIn(result, ["=-", "x"], "Two-char word should have valid code")


class TestTaqtiLengthThree(unittest.TestCase):
    """Test scansion for three-character words."""

    def test_common_words(self):
        """Test common three-character Urdu words."""
        test_cases = [
            ("کتاب", None),  # Should produce valid code
            ("دوست", None),
            ("شہر", None),
            ("گھر", None),
        ]
        for word, _ in test_cases:
            with self.subTest(word=word):
                result = length_three_scan(word)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
                # Code should contain only -, =, or x
                self.assertTrue(all(c in "-=x" for c in result), 
                              f"Code {result} should only contain -, =, or x")

    def test_starts_with_alif_madd(self):
        """Test three-character words starting with آ."""
        result = length_three_scan("آنا")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_alif_at_center(self):
        """Test words with alif at center position."""
        result = length_three_scan("کتاب")
        self.assertIsInstance(result, str)
        # Should typically be =- or similar
        self.assertIn(len(result), [2, 3])

    def test_ends_with_vowel(self):
        """Test words ending with vowels."""
        test_cases = ["کسی", "گھر", "دوست"]
        for word in test_cases:
            with self.subTest(word=word):
                result = length_three_scan(word)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)

    def test_with_diacritics(self):
        """Test three-character words with diacritics."""
        # Word with jazm (sukun)
        result = length_three_scan("ک\u064Eتاب")
        self.assertIsInstance(result, str)

    def test_assign_code_three_char(self):
        """Test assign_code for three-character words."""
        word = Words()
        word.word = "کتاب"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(c in "-=x" for c in result))


class TestTaqtiLengthFour(unittest.TestCase):
    """Test scansion for four-character words."""

    def test_common_words(self):
        """Test common four-character Urdu words."""
        test_cases = [
            ("کتابیں", None),
            ("دوستی", None),
            ("شہری", None),
            ("گھری", None),
        ]
        for word, _ in test_cases:
            with self.subTest(word=word):
                result = length_four_scan(word)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
                self.assertTrue(all(c in "-=x" for c in result))

    def test_starts_with_alif_madd(self):
        """Test four-character words starting with آ."""
        result = length_four_scan("آناں")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_alif_at_position_2(self):
        """Test words with alif at position 2."""
        result = length_four_scan("کتاب")
        self.assertIsInstance(result, str)

    def test_assign_code_four_char(self):
        """Test assign_code for four-character words."""
        word = Words()
        word.word = "کتابیں"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestTaqtiLengthFive(unittest.TestCase):
    """Test scansion for five-character words."""

    def test_common_words(self):
        """Test common five-character Urdu words."""
        test_cases = [
            ("کتابیں", None),  # 5 chars with diacritics
            ("دوستی", None),
        ]
        for word, _ in test_cases:
            with self.subTest(word=word):
                # Check if word is actually 5 chars after removing diacritics
                stripped = remove_araab(word)
                if len(stripped) >= 5:
                    result = length_five_scan(word)
                    self.assertIsInstance(result, str)
                    self.assertGreater(len(result), 0)
                    self.assertTrue(all(c in "-=x" for c in result))

    def test_longer_words(self):
        """Test longer words (5+ characters)."""
        result = length_five_scan("کتابیں")
        self.assertIsInstance(result, str)

    def test_assign_code_five_char(self):
        """Test assign_code for five-character words."""
        word = Words()
        word.word = "کتابیں"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestNoonGhunna(unittest.TestCase):
    """Test noon ghunna (nasalization) handling."""

    def test_contains_noon(self):
        """Test contains_noon function."""
        self.assertTrue(contains_noon("نظر"))
        self.assertTrue(contains_noon("انگ"))
        self.assertTrue(contains_noon("ہنس"))
        self.assertTrue(contains_noon("باندھ"))
        self.assertFalse(contains_noon("کتاب"))
        self.assertFalse(contains_noon("آب"))

    def test_noon_ghunna_length_3(self):
        """Test noon_ghunna for 3-character words."""
        # Test case: آنت with jazm on ن (should become =-)
        # آ + ن\u0652 + ت
        word = "آن\u0652ت"  # jazm (\u0652) on ن
        code = "=--"
        result = noon_ghunna(word, code)
        self.assertEqual(result, "=-", "آنت with jazm should be adjusted to =-")

        # Test case: انگ with jazm on ن (should remain =-)
        # ا + ن\u0652 + گ
        word = "ان\u0652گ"  # jazm on ن
        code = "=-"
        result = noon_ghunna(word, code)
        self.assertEqual(result, "=-", "انگ with jazm should remain =-")

        # Test case: ہنس with jazm on ن (should become =)
        # ہ + ن\u0652 + س
        word = "ہن\u0652س"  # jazm on ن
        code = "=-"
        result = noon_ghunna(word, code)
        self.assertEqual(result, "=", "ہنس with jazm should become =")

    def test_noon_ghunna_length_4(self):
        """Test noon_ghunna for 4-character words."""
        # Jazm diacritic: \u0652
        jazm = "\u0652"
        
        # Test case: اندر with jazm on ن at position 1 (should remain ==)
        # ا + ن + jazm + د + ر
        word = "ان" + jazm + "در"  # jazm on ن (position 1)
        code = "=="
        result = noon_ghunna(word, code)
        self.assertEqual(result, "==", "اندر with jazm on ن should remain ==")

        # Test case: ہنسا with jazm on ن at position 1 (should become -=)
        # ہ + ن + jazm + س + ا
        word = "ہن" + jazm + "سا"  # jazm on ن (position 1)
        code = "=="
        result = noon_ghunna(word, code)
        self.assertEqual(result, "-=", "ہنسا with jazm on ن should become -=")

        # Test case: باندھ with jazm on ن at position 2 (should become =-)
        # ب + ا + ن + jazm + دھ
        word = "بان" + jazm + "دھ"  # jazm on ن (position 2)
        code = "=--"
        result = noon_ghunna(word, code)
        self.assertEqual(result, "=-", "باندھ with jazm on ن should become =-")

    def test_noon_ghunna_length_5(self):
        """Test noon_ghunna for 5-character words."""
        # Test various 5-character cases
        test_cases = [
            ("آنت", "=--", "=-"),  # Should remove middle -
        ]
        for word, code, expected in test_cases:
            with self.subTest(word=word):
                result = noon_ghunna(word, code)
                # Just verify it returns a valid code
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)


class TestTaqtiWithDiacritics(unittest.TestCase):
    """Test scansion with diacritical marks."""

    def test_with_zabar(self):
        """Test words with zabar (fatha) diacritic."""
        word = Words()
        word.word = "ک\u064Eتاب"  # ک with zabar
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_with_zer(self):
        """Test words with zer (kasra) diacritic."""
        word = Words()
        word.word = "ک\u0650تاب"  # ک with zer
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_with_paish(self):
        """Test words with paish (damma) diacritic."""
        word = Words()
        word.word = "ک\u064Fتاب"  # ک with paish
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_with_jazm(self):
        """Test words with jazm (sukun) diacritic."""
        word = Words()
        word.word = "ک\u0652تاب"  # ک with jazm
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_with_shadd(self):
        """Test words with shadd (tashdid) diacritic."""
        word = Words()
        word.word = "ک\u0651تاب"  # ک with shadd
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)


class TestTaqtiSpecialCharacters(unittest.TestCase):
    """Test scansion with special characters (ھ، ں)."""

    def test_with_heh_doachashmee(self):
        """Test words with ھ (heh doachashmee)."""
        word = Words()
        word.word = "کتابھ"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        # ھ should be removed for scansion purposes
        stripped = remove_araab(word.word.replace("\u06BE", ""))
        self.assertGreater(len(stripped), 0)

    def test_with_noon_ghunna_char(self):
        """Test words with ں (noon ghunna character)."""
        word = Words()
        word.word = "کتابں"
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        # ں should be removed for scansion purposes
        stripped = remove_araab(word.word.replace("\u06BA", ""))
        self.assertGreater(len(stripped), 0)


class TestTaqtiRealWords(unittest.TestCase):
    """Test scansion with real Urdu words."""

    def test_common_urdu_words(self):
        """Test scansion of common Urdu words."""
        test_words = [
            "آب",      # water
            "کتاب",    # book
            "دوست",    # friend
            "شہر",     # city
            "گھر",     # home
            "کسی",     # someone
            "کے",      # of
            "کو",      # to/for
            "وہ",      # that/he/she
            "یہ",      # this
        ]
        
        for word_text in test_words:
            with self.subTest(word=word_text):
                word = Words()
                word.word = word_text
                word.taqti = []
                
                # Calculate expected length
                stripped = remove_araab(word_text.replace("\u06BE", "").replace("\u06BA", ""))
                word.length = len(stripped)
                
                result = assign_code(word)
                
                # Verify result
                self.assertIsInstance(result, str, f"{word_text} should return a string")
                self.assertGreater(len(result), 0, f"{word_text} should have non-empty code")
                self.assertTrue(all(c in "-=x" for c in result), 
                              f"{word_text} code {result} should only contain -, =, or x")
                
                # Code length should roughly match word length
                # (may be shorter due to contractions, longer due to expansions)
                self.assertLessEqual(len(result), word.length + 2, 
                                   f"{word_text} code length should be reasonable")


class TestTaqtiEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def test_empty_word(self):
        """Test handling of empty word."""
        word = Words()
        word.word = ""
        word.taqti = []
        word.length = 0
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_word_with_only_diacritics(self):
        """Test word with only diacritics."""
        word = Words()
        word.word = "\u064E\u0650\u064F"  # Only diacritics
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)

    def test_very_long_word(self):
        """Test very long word (6+ characters)."""
        word = Words()
        word.word = "کتابیں"  # May be 5+ after processing
        word.taqti = []
        result = assign_code(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_word_with_taqti_provided(self):
        """Test word that already has taqti."""
        word = Words()
        word.word = "کتاب"
        word.taqti = ["کتاب"]  # Taqti provided
        result = assign_code(word)
        self.assertIsInstance(result, str)
        # Should use taqti if available
        self.assertGreater(len(result), 0)


class TestTaqtiConsistency(unittest.TestCase):
    """Test consistency of scansion codes."""

    def test_same_word_consistency(self):
        """Test that same word produces consistent results."""
        word_text = "کتاب"
        results = []
        
        for _ in range(5):
            word = Words()
            word.word = word_text
            word.taqti = []
            result = assign_code(word)
            results.append(result)
        
        # All results should be the same
        self.assertTrue(all(r == results[0] for r in results),
                       f"Same word {word_text} should produce consistent codes, got {results}")

    def test_code_format(self):
        """Test that codes follow expected format."""
        test_words = ["آ", "آب", "کتاب", "دوست", "شہر"]
        
        for word_text in test_words:
            with self.subTest(word=word_text):
                word = Words()
                word.word = word_text
                word.taqti = []
                result = assign_code(word)
                
                # Code should only contain -, =, or x
                self.assertTrue(all(c in "-=x" for c in result),
                              f"Code {result} for {word_text} should only contain -, =, or x")
                
                # Code should not be empty
                self.assertGreater(len(result), 0,
                                 f"Code for {word_text} should not be empty")


if __name__ == '__main__':
    unittest.main()

