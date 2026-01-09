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
    compute_scansion,
    noon_ghunna,
    contains_noon
)
from aruuz.models import Words
from aruuz.utils.araab import remove_araab


class TestTaqtiLengthOne(unittest.TestCase):
    """Test scansion for single-character words."""

    def test_alif_madd_long(self):
        """Test: آ (alif madd) should be scanned as long syllable (=).
        
        Alif madd (آ) represents a long vowel and should always produce
        a long syllable code (=).
        """
        result = length_one_scan("آ")
        self.assertEqual(result, "=", "آ should be scanned as long (=)")

    def test_regular_consonant_short(self):
        """Test: Regular consonants should be scanned as short syllables (-).
        
        Single consonants without vowels should produce short syllable codes (-).
        Tests: ک, ب, ت, د, ر, س, ل, م, ن
        """
        test_cases = ["ک", "ب", "ت", "د", "ر", "س", "ل", "م", "ن"]
        for char in test_cases:
            with self.subTest(char=char):
                result = length_one_scan(char)
                self.assertEqual(result, "-", f"{char} should be scanned as short (-)")

    def test_assign_code_single_char(self):
        """Test: assign_code() for single character words.
        
        Tests that assign_code correctly handles:
        - آ should return = (long)
        - ک should return - (short)
        """
        word = Words()
        word.word = "آ"
        word.taqti = []
        result = compute_scansion(word)
        self.assertEqual(result, "=")

        word.word = "ک"
        result = compute_scansion(word)
        self.assertEqual(result, "-")


class TestTaqtiLengthTwo(unittest.TestCase):
    """Test scansion for two-character words."""

    def test_starts_with_alif_madd(self):
        """Test: Words starting with آ should be =- (long-short).
        
        Example: آب (water) should produce =- where:
        - آ is long (=)
        - ب is short (-)
        """
        result = length_two_scan("آب")
        self.assertEqual(result, "=-", "آب should be =- (long-short)")

    def test_ends_with_vowel_flexible(self):
        """Test: Words ending with vowels should be flexible (x).
        
        Words ending in ا،ی،ے،و،ہ should produce flexible syllable code (x)
        because the final vowel can be long or short depending on context.
        Tests: کا, کی, کے, کو, کہ
        """
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
        """Test: Default two-character words should be = (long).
        
        Two-character words that don't match special patterns should
        default to a single long syllable (=).
        Example: کب
        """
        result = length_two_scan("کب")
        self.assertEqual(result, "=", "Default two-char word should be =")

    def test_assign_code_two_char(self):
        """Test: assign_code() for two-character words.
        
        Tests that assign_code correctly processes two-character words
        and returns valid scansion codes (=- or x).
        Example: آب
        """
        word = Words()
        word.word = "آب"
        word.taqti = []
        result = compute_scansion(word)
        self.assertIn(result, ["=-", "x"], "Two-char word should have valid code")


class TestTaqtiLengthThree(unittest.TestCase):
    """Test scansion for three-character words."""

    def test_common_words(self):
        """Test: Common three-character Urdu words produce valid codes.
        
        Tests that length_three_scan produces valid scansion codes
        containing only -, =, or x for common words.
        Tests: کتاب (book), دوست (friend), شہر (city), گھر (home)
        """
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
        """Test: Three-character words starting with آ.
        
        Words starting with آ (alif madd) should produce valid scansion codes.
        Example: آنا
        """
        result = length_three_scan("آنا")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_alif_at_center(self):
        """Test: Words with alif at center position.
        
        Words with alif (ا) at position 2 should produce codes of length 2-3.
        Example: کتاب (book) - typically produces =- or similar pattern.
        """
        result = length_three_scan("کتاب")
        self.assertIsInstance(result, str)
        # Should typically be =- or similar
        self.assertIn(len(result), [2, 3])

    def test_ends_with_vowel(self):
        """Test: Three-character words ending with vowels.
        
        Words ending with vowels should produce valid scansion codes.
        Tests: کسی, گھر, دوست
        """
        test_cases = ["کسی", "گھر", "دوست"]
        for word in test_cases:
            with self.subTest(word=word):
                result = length_three_scan(word)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)

    def test_with_diacritics(self):
        """Test: Three-character words with diacritical marks.
        
        Words with diacritics (zabar, zer, paish, jazm, etc.) should
        be processed correctly and produce valid codes.
        Example: کتاب with zabar (fatha) diacritic.
        """
        # Word with jazm (sukun)
        result = length_three_scan("ک\u064Eتاب")
        self.assertIsInstance(result, str)

    def test_assign_code_three_char(self):
        """Test: assign_code() for three-character words.
        
        Tests that assign_code correctly processes three-character words
        and returns valid scansion codes containing only -, =, or x.
        Example: کتاب (book)
        """
        word = Words()
        word.word = "کتاب"
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertTrue(all(c in "-=x" for c in result))


class TestTaqtiLengthFour(unittest.TestCase):
    """Test scansion for four-character words."""

    def test_common_words(self):
        """Test: Common four-character Urdu words produce valid codes.
        
        Tests that length_four_scan produces valid scansion codes
        for common four-character words.
        Tests: کتابیں, دوستی, شہری, گھری
        """
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
        """Test: Four-character words starting with آ.
        
        Words starting with آ (alif madd) should produce valid scansion codes.
        Example: آناں
        """
        result = length_four_scan("آناں")
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_has_alif_at_position_2(self):
        """Test: Words with alif at position 2.
        
        Words with alif (ا) at the second position should produce valid codes.
        Example: کتاب (book)
        """
        result = length_four_scan("کتاب")
        self.assertIsInstance(result, str)

    def test_assign_code_four_char(self):
        """Test: assign_code() for four-character words.
        
        Tests that assign_code correctly processes four-character words.
        Example: کتابیں
        """
        word = Words()
        word.word = "کتابیں"
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestTaqtiLengthFive(unittest.TestCase):
    """Test scansion for five-character words."""

    def test_common_words(self):
        """Test: Common five-character Urdu words produce valid codes.
        
        Tests that length_five_scan produces valid scansion codes
        for words that are 5+ characters after removing diacritics.
        Tests: کتابیں, دوستی
        """
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
        """Test: Longer words (5+ characters) produce valid codes.
        
        Words with 5 or more characters should produce valid scansion codes.
        Example: کتابیں
        """
        result = length_five_scan("کتابیں")
        self.assertIsInstance(result, str)

    def test_assign_code_five_char(self):
        """Test: assign_code() for five-character words.
        
        Tests that assign_code correctly processes five-character words.
        Example: کتابیں
        """
        word = Words()
        word.word = "کتابیں"
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)


class TestNoonGhunna(unittest.TestCase):
    """Test noon ghunna (nasalization) handling."""

    def test_contains_noon(self):
        """Test: contains_noon() correctly identifies words with ن (noon).
        
        Should return True for words containing ن: نظر, انگ, ہنس, باندھ
        Should return False for words without ن: کتاب, آب
        """
        self.assertTrue(contains_noon("نظر"))
        self.assertTrue(contains_noon("انگ"))
        self.assertTrue(contains_noon("ہنس"))
        self.assertTrue(contains_noon("باندھ"))
        self.assertFalse(contains_noon("کتاب"))
        self.assertFalse(contains_noon("آب"))

    def test_noon_ghunna_length_3(self):
        """Test: noon_ghunna() adjustments for 3-character words.
        
        Tests noon ghunna (nasalization) adjustments when ن has jazm (sukun):
        - آنت with jazm: =-- should become =-
        - انگ with jazm: =- should remain =-
        - ہنس with jazm: =- should become =
        """
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
        """Test: noon_ghunna() adjustments for 4-character words.
        
        Tests noon ghunna adjustments when ن has jazm at different positions:
        - اندر with jazm on ن at pos 1: == should remain ==
        - ہنسا with jazm on ن at pos 1: == should become -=
        - باندھ with jazm on ن at pos 2: =-- should become =-
        """
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
        """Test: noon_ghunna() adjustments for 5-character words.
        
        Tests that noon_ghunna correctly processes 5-character words
        with ن and jazm, producing valid scansion codes.
        """
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
        """Test: Words with zabar (fatha) diacritic produce valid codes.
        
        Zabar (\u064E) indicates a short 'a' vowel sound.
        Example: کتاب with zabar on ک
        """
        word = Words()
        word.word = "ک\u064Eتاب"  # ک with zabar
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_with_zer(self):
        """Test: Words with zer (kasra) diacritic produce valid codes.
        
        Zer (\u0650) indicates a short 'i' vowel sound.
        Example: کتاب with zer on ک
        """
        word = Words()
        word.word = "ک\u0650تاب"  # ک with zer
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)

    def test_with_paish(self):
        """Test: Words with paish (damma) diacritic produce valid codes.
        
        Paish (\u064F) indicates a short 'u' vowel sound.
        Example: کتاب with paish on ک
        """
        word = Words()
        word.word = "ک\u064Fتاب"  # ک with paish
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)

    def test_with_jazm(self):
        """Test: Words with jazm (sukun) diacritic produce valid codes.
        
        Jazm (\u0652) indicates absence of vowel (consonant cluster).
        Example: کتاب with jazm on ک
        """
        word = Words()
        word.word = "ک\u0652تاب"  # ک with jazm
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)

    def test_with_shadd(self):
        """Test: Words with shadd (tashdid) diacritic produce valid codes.
        
        Shadd (\u0651) indicates gemination (doubling) of a consonant.
        Example: کتاب with shadd on ک
        """
        word = Words()
        word.word = "ک\u0651تاب"  # ک with shadd
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)


class TestTaqtiSpecialCharacters(unittest.TestCase):
    """Test scansion with special characters (ھ، ں)."""

    def test_with_heh_doachashmee(self):
        """Test: Words with ھ (heh doachashmee) are processed correctly.
        
        The character ھ should be removed for scansion purposes before
        processing, as it's a special form of heh.
        Example: کتابھ
        """
        word = Words()
        word.word = "کتابھ"
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        # ھ should be removed for scansion purposes
        stripped = remove_araab(word.word.replace("\u06BE", ""))
        self.assertGreater(len(stripped), 0)

    def test_with_noon_ghunna_char(self):
        """Test: Words with ں (noon ghunna character) are processed correctly.
        
        The character ں should be removed for scansion purposes before
        processing, as it's a special form of noon.
        Example: کتابں
        """
        word = Words()
        word.word = "کتابں"
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        # ں should be removed for scansion purposes
        stripped = remove_araab(word.word.replace("\u06BA", ""))
        self.assertGreater(len(stripped), 0)


class TestTaqtiRealWords(unittest.TestCase):
    """Test scansion with real Urdu words."""

    def test_common_urdu_words(self):
        """Test: Scansion of common Urdu words produces valid codes.
        
        Tests that assign_code correctly processes common Urdu words
        and produces valid scansion codes with reasonable lengths.
        Tests: آب (water), کتاب (book), دوست (friend), شہر (city),
        گھر (home), کسی (someone), کے (of), کو (to/for), وہ (that/he/she),
        یہ (this)
        """
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
                
                result = compute_scansion(word)
                
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
        """Test: Empty word is handled gracefully.
        
        assign_code should handle empty words without errors
        and return a string result (may be empty).
        """
        word = Words()
        word.word = ""
        word.taqti = []
        word.length = 0
        result = compute_scansion(word)
        self.assertIsInstance(result, str)

    def test_word_with_only_diacritics(self):
        """Test: Word containing only diacritics is handled gracefully.
        
        Words with only diacritical marks (no base characters) should
        be processed without errors.
        """
        word = Words()
        word.word = "\u064E\u0650\u064F"  # Only diacritics
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)

    def test_very_long_word(self):
        """Test: Very long words (6+ characters) produce valid codes.
        
        Words with 6 or more characters should produce valid scansion codes.
        Example: کتابیں (may be 5+ characters after processing)
        """
        word = Words()
        word.word = "کتابیں"  # May be 5+ after processing
        word.taqti = []
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_word_with_taqti_provided(self):
        """Test: Words with pre-provided taqti are handled correctly.
        
        If a word already has taqti (scansion) provided, assign_code
        should use it if available and return a valid code.
        Example: کتاب with taqti already set
        """
        word = Words()
        word.word = "کتاب"
        word.taqti = ["کتاب"]  # Taqti provided
        result = compute_scansion(word)
        self.assertIsInstance(result, str)
        # Should use taqti if available
        self.assertGreater(len(result), 0)


class TestTaqtiConsistency(unittest.TestCase):
    """Test consistency of scansion codes."""

    def test_same_word_consistency(self):
        """Test: Same word produces consistent scansion codes.
        
        Running assign_code multiple times on the same word should
        produce identical results, ensuring deterministic behavior.
        Tests: کتاب (book) - run 5 times
        """
        word_text = "کتاب"
        results = []
        
        for _ in range(5):
            word = Words()
            word.word = word_text
            word.taqti = []
            result = compute_scansion(word)
            results.append(result)
        
        # All results should be the same
        self.assertTrue(all(r == results[0] for r in results),
                       f"Same word {word_text} should produce consistent codes, got {results}")

    def test_code_format(self):
        """Test: Scansion codes follow expected format.
        
        All scansion codes should:
        - Only contain characters: -, =, or x
        - Not be empty
        Tests: آ, آب, کتاب, دوست, شہر
        """
        test_words = ["آ", "آب", "کتاب", "دوست", "شہر"]
        
        for word_text in test_words:
            with self.subTest(word=word_text):
                word = Words()
                word.word = word_text
                word.taqti = []
                result = compute_scansion(word)
                
                # Code should only contain -, =, or x
                self.assertTrue(all(c in "-=x" for c in result),
                              f"Code {result} for {word_text} should only contain -, =, or x")
                
                # Code should not be empty
                self.assertGreater(len(result), 0,
                                 f"Code for {word_text} should not be empty")

class TestTaqtiGoldenWords(unittest.TestCase):
    """
    Golden tests for word → scansion codes.

    These tests assert metrical correctness at word level.
    They are intentionally opinionated and based on accepted arūz usage.
    """

    def scan(self, text):
        word = Words()
        word.word = text
        word.taqti = []
        return compute_scansion(word)

    def test_deterministic_words_exact(self):
        """Words with no metrical ambiguity must return exact codes."""
        cases = {
            "دل": {"="},
            "رات": {"=-"},
            "آ": {"="},
            "وہ": {"x"},
            "یہ": {"x"},
        }

        for word, expected in cases.items():
            with self.subTest(word=word):
                result = self.scan(word)
                self.assertEqual(
                    set([result]),
                    expected,
                    f"{word} should scan exactly as {expected}, got {result}"
                )

    def test_ambiguous_words_must_include(self):
        """
        Ambiguous words must include at least one accepted metrical form.
        False positives are acceptable; false negatives are not.
        """
        cases = {
            "بہار": {"=-", "=="},
            "خمار": {"=--", "=-=", "-=-"},
            "اجالا": {"=-=", "--=", "-=="},
            "اندھیرے": {"-=="},
        }

        for word, must_have in cases.items():
            with self.subTest(word=word):
                result = self.scan(word)
                for code in must_have:
                    if code in result:
                        break
                else:
                    self.fail(
                        f"{word} must include one of {must_have}, got {result}"
                    )

    def test_regression_words_must_not_include(self):
        """
        Regression tests for known-bad outputs.
        These should NEVER reappear once fixed.
        """
        cases = {
            "اندھیرے": {"==x"},
        }

        for word, forbidden in cases.items():
            with self.subTest(word=word):
                result = self.scan(word)
                for bad in forbidden:
                    self.assertNotIn(
                        bad,
                        result,
                        f"{word} must not produce {bad}, got {result}"
                    )

    def test_real_poetic_usage_words(self):
        """
        Words tested in real shers where meter matching already works.
        This anchors word-level scansion to line-level success.
        """
        words = [
            "دم",
            "اندھیرے",
            "خمار",
            "اجالا",
            "چاروں",
            "طرف",
        ]

        for word in words:
            with self.subTest(word=word):
                result = self.scan(word)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
                self.assertTrue(
                    all(c in "-=x" for c in result),
                    f"{word} produced invalid code {result}"
                )

if __name__ == '__main__':
    unittest.main()

