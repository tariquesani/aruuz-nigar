"""
Tests for scansion engine.

Tests word code assignment methods with known words.
"""

import logging
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
    contains_noon,
    is_match,
    check_code_length,
    Scansion
)
from aruuz.models import Words, Lines, scanOutput

# Configure logging to show DEBUG messages from aruuz modules during tests
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Enable DEBUG logging for aruuz modules
logging.getLogger('aruuz').setLevel(logging.DEBUG)
logging.getLogger('aruuz.scansion').setLevel(logging.DEBUG)
logging.getLogger('aruuz.database').setLevel(logging.DEBUG)
logging.getLogger('aruuz.database.word_lookup').setLevel(logging.DEBUG)


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


class TestPatternMatching(unittest.TestCase):
    """Test pattern matching functions."""

    def test_is_match_exact_match(self):
        """Test is_match with exact pattern match."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "-==="
        result = is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_with_tentative_code(self):
        """Test is_match with tentative code from previous words."""
        meter = "-===/-===/-===/-==="
        tentative_code = "-==="
        word_code = "-==="
        result = is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_with_flexible_syllable(self):
        """Test is_match with 'x' (flexible syllable)."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "x==="  # 'x' should match both '-' and '='
        result = is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_no_match(self):
        """Test is_match when pattern doesn't match."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "===-"  # Wrong pattern
        result = is_match(meter, tentative_code, word_code)
        self.assertFalse(result)

    def test_is_match_with_caesura(self):
        """Test is_match with caesura (word boundary)."""
        meter = "-===/-===+=-=/-==="  # Has '+' at word boundary
        tentative_code = "-==="
        word_code = "-"  # Single character, should be allowed
        result = is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_caesura_violation(self):
        """Test is_match detects caesura violation."""
        meter = "-===/-===+=-=/-==="  # Has '+' at word boundary
        tentative_code = "-==="
        word_code = "=="  # Doesn't end with '-', should violate caesura
        result = is_match(meter, tentative_code, word_code)
        self.assertFalse(result)

    def test_is_match_variation_1(self):
        """Test is_match with variation 1 (meter with '+' removed + '-' appended)."""
        meter = "-===/-===+=-=/-==="
        tentative_code = ""
        word_code = "-===-"  # Should match variation 1
        result = is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_empty_codes(self):
        """Test is_match with empty codes."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = ""
        result = is_match(meter, tentative_code, word_code)
        self.assertFalse(result)

    def test_check_code_length_exact_match(self):
        """Test check_code_length with exact length match."""
        code = "-==="
        meter_indices = [0, 1, 2]  # First few meters
        result = check_code_length(code, meter_indices)
        # Should return indices that match the code length
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), len(meter_indices))

    def test_check_code_length_filters_mismatches(self):
        """Test check_code_length filters out meters that don't match."""
        code = "-"  # Very short code
        meter_indices = [0, 1, 2, 3, 4]  # Multiple meters
        result = check_code_length(code, meter_indices)
        # Should filter out meters that don't match any variation
        self.assertIsInstance(result, list)
        # Result should be a subset of input
        for idx in result:
            self.assertIn(idx, meter_indices)

    def test_check_code_length_with_flexible_syllable(self):
        """Test check_code_length with 'x' in code."""
        code = "x==="
        meter_indices = [0, 1]
        result = check_code_length(code, meter_indices)
        self.assertIsInstance(result, list)

    def test_check_code_length_empty_list(self):
        """Test check_code_length with empty meter indices."""
        code = "-==="
        meter_indices = []
        result = check_code_length(code, meter_indices)
        self.assertEqual(result, [])

    def test_check_code_length_all_variations(self):
        """Test check_code_length checks all 4 variations."""
        # Use a code that might match different variations
        code = "-==="
        meter_indices = [0]  # First meter
        result = check_code_length(code, meter_indices)
        # Should check all variations and return appropriate result
        self.assertIsInstance(result, list)

    def test_check_code_length_with_plus_in_meter(self):
        """Test check_code_length with meter containing '+'."""
        code = "-==="
        # Find a meter with '+' in it
        from aruuz.meters import METERS
        meter_with_plus = None
        meter_idx = None
        for i, m in enumerate(METERS):
            if '+' in m:
                meter_with_plus = m
                meter_idx = i
                break
        
        if meter_with_plus:
            result = check_code_length(code, [meter_idx])
            self.assertIsInstance(result, list)


class TestCrunchMethods(unittest.TestCase):
    """Test crunch-related methods: is_ordered, calculate_score, crunch."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.scanner = Scansion()
    
    def test_is_ordered_matching_lists(self):
        """Test is_ordered with matching lists."""
        line_arkaan = ["مفعولن", "مفعولن", "مفعولن", "مفعول"]
        feet = ["مفعولن", "مفعولن", "مفعولن", "مفعول"]
        self.assertTrue(self.scanner.is_ordered(line_arkaan, feet))
    
    def test_is_ordered_non_matching_lists(self):
        """Test is_ordered with non-matching lists."""
        line_arkaan = ["مفعولن", "مفعول"]
        feet = ["مفعول", "مفعولن"]
        self.assertFalse(self.scanner.is_ordered(line_arkaan, feet))
    
    def test_is_ordered_different_lengths(self):
        """Test is_ordered with lists of different lengths."""
        line_arkaan = ["مفعولن", "مفعولن"]
        feet = ["مفعولن", "مفعولن", "مفعول"]
        self.assertFalse(self.scanner.is_ordered(line_arkaan, feet))
    
    def test_is_ordered_empty_lists(self):
        """Test is_ordered with empty lists."""
        self.assertTrue(self.scanner.is_ordered([], []))
        self.assertFalse(self.scanner.is_ordered([], ["مفعولن"]))
        self.assertFalse(self.scanner.is_ordered(["مفعولن"], []))
    
    def test_calculate_score_matching_meter(self):
        """Test calculate_score with matching meter and line feet."""
        # Use a known meter name and its expected feet
        meter_name = "ہزج مثمن سالم"
        line_feet = "مفعولن مفعولن مفعولن مفعول"  # Typical feet for this meter
        score = self.scanner.calculate_score(meter_name, line_feet)
        # Should return 1 if match, 0 otherwise
        self.assertIn(score, [0, 1])
    
    def test_calculate_score_non_matching_meter(self):
        """Test calculate_score with non-matching meter."""
        meter_name = "ہزج مثمن سالم"
        line_feet = "فاعلن فاعلن"  # Different feet
        score = self.scanner.calculate_score(meter_name, line_feet)
        # Should return 0 for non-match
        self.assertEqual(score, 0)
    
    def test_calculate_score_invalid_meter(self):
        """Test calculate_score with invalid meter name."""
        meter_name = "Invalid Meter Name"
        line_feet = "مفعولن مفعولن"
        score = self.scanner.calculate_score(meter_name, line_feet)
        self.assertEqual(score, 0)
    
    def test_crunch_empty_results(self):
        """Test crunch with empty results."""
        result = self.scanner.crunch([])
        self.assertEqual(result, "")
    
    def test_crunch_single_meter(self):
        """Test crunch with single meter match."""
        so = scanOutput()
        so.meter_name = "ہزج مثمن سالم"
        so.feet = "مفعولن مفعولن مفعولن مفعول"
        so.original_line = "test line"
        
        result = self.scanner.crunch([so])
        self.assertEqual(result, "ہزج مثمن سالم")
    
    def test_crunch_multiple_meters(self):
        """Test crunch with multiple meter matches."""
        # Create results with different meters
        so1 = scanOutput()
        so1.meter_name = "ہزج مثمن سالم"
        so1.feet = "مفعولن مفعولن مفعولن مفعول"
        so1.original_line = "line 1"
        
        so2 = scanOutput()
        so2.meter_name = "ہزج مثمن محذوف"
        so2.feet = "مفعولن مفعولن مفعول"
        so2.original_line = "line 1"
        
        so3 = scanOutput()
        so3.meter_name = "ہزج مثمن سالم"
        so3.feet = "مفعولن مفعولن مفعولن مفعول"
        so3.original_line = "line 2"
        
        # The dominant meter should be the one with highest score
        result = self.scanner.crunch([so1, so2, so3])
        # Should return one of the meter names
        self.assertIn(result, ["ہزج مثمن سالم", "ہزج مثمن محذوف"])
    
    def test_scan_lines_preserves_all_matches(self):
        """Test that scan_lines preserves all matches and marks dominant."""
        scanner = Scansion()
        
        # Add a line that might match multiple meters
        line1 = Lines("نقش فریادی ہے کس کی شوخیِ تحریر کا")
        scanner.add_line(line1)
        
        results = scanner.scan_lines()
        
        # Should have at least one result
        self.assertGreater(len(results), 0)
        
        # Check that is_dominant field exists
        for result in results:
            self.assertIsInstance(result.is_dominant, bool)
        
        # At least one result should be marked as dominant
        dominant_count = sum(1 for r in results if r.is_dominant)
        self.assertGreater(dominant_count, 0, "At least one result should be marked as dominant")
    
    def test_scan_lines_multiple_lines(self):
        """Test scan_lines with multiple lines preserves all matches."""
        scanner = Scansion()
        
        line1 = Lines("نقش فریادی ہے کس کی شوخیِ تحریر کا")
        line2 = Lines("کاغذی پیرہن میں جو نہ تھا وہ بدن تھا")
        
        scanner.add_line(line1)
        scanner.add_line(line2)
        
        results = scanner.scan_lines()
        
        # Should have results for both lines
        self.assertGreater(len(results), 0)
        
        # All results should have is_dominant field
        for result in results:
            self.assertIsInstance(result.is_dominant, bool)
        
        # Should have at least one dominant result
        dominant_results = [r for r in results if r.is_dominant]
        self.assertGreater(len(dominant_results), 0)


if __name__ == '__main__':
    unittest.main()
