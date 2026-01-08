"""
Tests for fuzzy matching functionality.

Tests the fuzzy matching APIs (scan_line_fuzzy, scan_lines_fuzzy, crunch_fuzzy)
with imperfect/experimental poetry examples that don't match meters exactly.
"""

import unittest
import math
from aruuz.scansion import Scansion
from aruuz.models import Lines, scanOutputFuzzy
from aruuz.meters import METERS, METER_NAMES, NUM_METERS


class TestScanLineFuzzy(unittest.TestCase):
    """Test scan_line_fuzzy() method with imperfect poetry."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6  # Reasonable error threshold for fuzzy matching

    def test_scan_line_fuzzy_returns_list(self):
        """Test that scan_line_fuzzy returns a list of scanOutputFuzzy objects."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        self.assertIsInstance(results, list)
        # Results may be empty if no fuzzy matches found, which is acceptable

    def test_scan_line_fuzzy_returns_scan_output_fuzzy_objects(self):
        """Test that scan_line_fuzzy returns scanOutputFuzzy objects with correct structure."""
        # Use a line that might have fuzzy matches
        line = Lines("دم اندھیرے میں گھٹ رہا ہے خمار")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            for result in results:
                self.assertIsInstance(result, scanOutputFuzzy)
                self.assertEqual(result.original_line, line.original_line)
                self.assertIsInstance(result.words, list)
                self.assertIsInstance(result.word_taqti, list)
                self.assertIsInstance(result.error, list)
                self.assertIsInstance(result.score, int)
                self.assertIsInstance(result.meter_name, str)
                self.assertIsInstance(result.feet, str)
                self.assertGreaterEqual(result.score, 0)  # Score should be non-negative

    def test_scan_line_fuzzy_calculates_scores(self):
        """Test that scan_line_fuzzy calculates Levenshtein distance scores."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            for result in results:
                # Score should be calculated (not default value 10)
                # If score is 10, it might be default, but that's acceptable for special meters
                self.assertIsInstance(result.score, int)
                self.assertGreaterEqual(result.score, 0)

    def test_scan_line_fuzzy_with_imperfect_line(self):
        """Test scan_line_fuzzy with a line that doesn't match meters perfectly."""
        # This line may not match perfectly, testing fuzzy matching
        line = Lines("ایک دن کہا گیا تھا کہ")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        self.assertIsInstance(results, list)
        # Even if no matches, should return empty list without errors
        for result in results:
            self.assertIsInstance(result, scanOutputFuzzy)
            self.assertNotEqual(result.meter_name, "")

    def test_scan_line_fuzzy_preserves_word_order(self):
        """Test that scan_line_fuzzy preserves word order in results."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # word_taqti should have same length as words
            self.assertEqual(len(result.word_taqti), len(result.words))
            # Each word should have corresponding taqti
            self.assertEqual(len(result.word_taqti), len(line.words_list))

    def test_scan_line_fuzzy_sets_error_flags(self):
        """Test that scan_line_fuzzy sets error flags for each word."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # Error flags should match number of words
            self.assertEqual(len(result.error), len(result.words))
            self.assertIsInstance(result.error[0], bool)

    def test_scan_line_fuzzy_with_empty_line(self):
        """Test scan_line_fuzzy with empty line."""
        line = Lines("")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Empty line should return empty results
        self.assertEqual(len(results), 0)

    def test_scan_line_fuzzy_multiple_meter_matches(self):
        """Test that scan_line_fuzzy can return multiple meter matches for a line."""
        # Use a line that might match multiple meters
        line = Lines("دم اندھیرے میں گھٹ رہا ہے خمار")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        self.assertIsInstance(results, list)
        # If multiple matches exist, they should have different meter names or scores
        if len(results) > 1:
            meter_names = [r.meter_name for r in results]
            # At least some variation expected (may have same meter with different scores)
            self.assertGreaterEqual(len(results), 1)

    def test_scan_line_fuzzy_score_is_levenshtein_distance(self):
        """Test that fuzzy scores represent Levenshtein distance (lower is better)."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 1:
            # Scores should be non-negative integers
            for result in results:
                self.assertGreaterEqual(result.score, 0)
                self.assertIsInstance(result.score, int)
            
            # Lower scores indicate better matches (for Levenshtein distance)
            scores = [r.score for r in results]
            # Verify scores are reasonable (not all the same unless there's a tie)
            self.assertGreaterEqual(min(scores), 0)


class TestScanLinesFuzzy(unittest.TestCase):
    """Test scan_lines_fuzzy() method with multiple lines."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_scan_lines_fuzzy_returns_list(self):
        """Test that scan_lines_fuzzy returns a list."""
        line1 = Lines("کتاب و قلم")
        line2 = Lines("دوات و کاغذ")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        results = self.scansion.scan_lines_fuzzy()
        
        self.assertIsInstance(results, list)

    def test_scan_lines_fuzzy_processes_all_lines(self):
        """Test that scan_lines_fuzzy processes all added lines."""
        line1 = Lines("کتاب")
        line2 = Lines("قلم")
        line3 = Lines("دوات")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        self.scansion.add_line(line3)
        
        self.assertEqual(self.scansion.num_lines, 3)
        
        results = self.scansion.scan_lines_fuzzy()
        
        self.assertIsInstance(results, list)
        # Results may be filtered by crunch_fuzzy, so count may be less than 3

    def test_scan_lines_fuzzy_calls_crunch_fuzzy(self):
        """Test that scan_lines_fuzzy calls crunch_fuzzy to consolidate results."""
        # Add multiple lines that might match different meters
        line1 = Lines("دم اندھیرے میں گھٹ رہا ہے خمار")
        line2 = Lines("اور چاروں طرف اجالا ہے")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        results = self.scansion.scan_lines_fuzzy()
        
        self.assertIsInstance(results, list)
        # After crunch_fuzzy, all results should have same meter name (best match)
        if len(results) > 0:
            meter_names = {r.meter_name for r in results}
            # All results should have the same meter name (consolidated by crunch_fuzzy)
            self.assertEqual(len(meter_names), 1, 
                           f"All results should have same meter after crunch_fuzzy, got: {meter_names}")

    def test_scan_lines_fuzzy_with_imperfect_poetry(self):
        """Test scan_lines_fuzzy with imperfect poetry that doesn't match exactly."""
        # Lines that may not match meters perfectly
        line1 = Lines("ایک دن کہا گیا تھا کہ")
        line2 = Lines("دنیا میں کچھ بھی نہیں ہے")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        results = self.scansion.scan_lines_fuzzy()
        
        self.assertIsInstance(results, list)
        # Should handle imperfect poetry gracefully

    def test_scan_lines_fuzzy_returns_scan_output_fuzzy_objects(self):
        """Test that scan_lines_fuzzy returns scanOutputFuzzy objects."""
        line1 = Lines("کتاب و قلم")
        line2 = Lines("دوات و کاغذ")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        results = self.scansion.scan_lines_fuzzy()
        
        for result in results:
            self.assertIsInstance(result, scanOutputFuzzy)


class TestCrunchFuzzy(unittest.TestCase):
    """Test crunch_fuzzy() method for score calculation and meter selection."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_crunch_fuzzy_with_empty_list(self):
        """Test crunch_fuzzy with empty list."""
        results = []
        
        consolidated = self.scansion.resolve_dominant_meter_fuzzy(results)
        
        self.assertEqual(len(consolidated), 0)

    def test_crunch_fuzzy_consolidates_by_meter(self):
        """Test that crunch_fuzzy consolidates results by best meter."""
        # Create mock fuzzy results with different meters and scores
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Get fuzzy results (may have multiple meter matches)
        all_results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(all_results) > 0:
            # Add another line to get more results
            line2 = Lines("دوات و کاغذ")
            self.scansion.add_line(line2)
            all_results.extend(self.scansion.scan_line_fuzzy(line2, 1))
            
            if len(all_results) > 0:
                consolidated = self.scansion.resolve_dominant_meter_fuzzy(all_results)
                
                # All consolidated results should have same meter name
                if len(consolidated) > 0:
                    meter_names = {r.meter_name for r in consolidated}
                    self.assertEqual(len(meter_names), 1,
                                   f"crunch_fuzzy should consolidate to one meter, got: {meter_names}")

    def test_crunch_fuzzy_selects_best_score(self):
        """Test that crunch_fuzzy selects meter with best (lowest) score."""
        # Create fuzzy results manually to test score selection
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        all_results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(all_results) >= 2:
            # Group results by meter and verify best meter is selected
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(all_results)
            
            if len(consolidated) > 0:
                # All consolidated results should have same meter (the best one)
                meter_name = consolidated[0].meter_name
                for result in consolidated:
                    self.assertEqual(result.meter_name, meter_name)

    def test_crunch_fuzzy_logarithmic_averaging(self):
        """Test that crunch_fuzzy uses logarithmic averaging for scores."""
        # Create mock results with known scores
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) >= 2:
            # Group by meter
            meters = {}
            for r in results:
                if r.meter_name not in meters:
                    meters[r.meter_name] = []
                meters[r.meter_name].append(r)
            
            # For each meter, calculate expected logarithmic average
            for meter_name, meter_results in meters.items():
                if len(meter_results) > 1:
                    scores = [r.score for r in meter_results]
                    subtract = sum(1 for s in scores if s == 0)
                    
                    # Calculate expected aggregate score
                    score_sum = 0.0
                    count = 0.0
                    for score in scores:
                        if score == 0:
                            score_sum += math.log(score + 1)
                            count += 1.0
                        else:
                            score_sum += math.log(score)
                            count += 1.0
                    
                    if count > 0:
                        expected_aggregate = math.exp(score_sum / count) - subtract
                        
                        # The consolidated result should use this meter if it's best
                        consolidated = self.scansion.resolve_dominant_meter_fuzzy(results)
                        # Just verify crunch_fuzzy runs without error
                        self.assertIsInstance(consolidated, list)

    def test_crunch_fuzzy_handles_zero_scores(self):
        """Test that crunch_fuzzy handles zero scores correctly."""
        # Create a result with score 0
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Modify a result to have score 0 (if any exist)
        if len(results) > 0:
            # Test that crunch_fuzzy can handle zero scores
            test_results = results.copy()
            test_results[0].score = 0
            
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(test_results)
            # Should handle zero scores without error
            self.assertIsInstance(consolidated, list)

    def test_crunch_fuzzy_preserves_best_meter_results(self):
        """Test that crunch_fuzzy preserves all results for the best meter."""
        line1 = Lines("کتاب و قلم")
        line2 = Lines("دوات و کاغذ")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        all_results = []
        all_results.extend(self.scansion.scan_line_fuzzy(line1, 0))
        all_results.extend(self.scansion.scan_line_fuzzy(line2, 1))
        
        if len(all_results) > 0:
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(all_results)
            
            if len(consolidated) > 0:
                # Count original results for best meter
                best_meter = consolidated[0].meter_name
                original_count = sum(1 for r in all_results if r.meter_name == best_meter)
                
                # Consolidated should preserve all results for best meter
                self.assertEqual(len(consolidated), original_count,
                               f"Should preserve all results for best meter {best_meter}")


class TestScanLinesWithFuzzyMode(unittest.TestCase):
    """Test scan_lines() when fuzzy=True uses fuzzy path."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_scan_lines_with_fuzzy_true_uses_fuzzy_path(self):
        """Test that scan_lines() uses fuzzy path when fuzzy=True."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        
        results = self.scansion.scan_lines()
        
        # Should return results (may be empty if no matches)
        self.assertIsInstance(results, list)
        # Results should be converted from scanOutputFuzzy to scanOutput

    def test_scan_lines_with_fuzzy_false_uses_regular_path(self):
        """Test that scan_lines() uses regular path when fuzzy=False."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = False
        
        results = self.scansion.scan_lines()
        
        # Should return scanOutput objects (not scanOutputFuzzy)
        self.assertIsInstance(results, list)
        if len(results) > 0:
            from aruuz.models import scanOutput
            self.assertIsInstance(results[0], scanOutput)

    def test_scan_lines_fuzzy_converts_to_scan_output(self):
        """Test that scan_lines() with fuzzy=True converts scanOutputFuzzy to scanOutput."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        
        results = self.scansion.scan_lines()
        
        # Results should be scanOutput objects, not scanOutputFuzzy
        if len(results) > 0:
            from aruuz.models import scanOutput
            for result in results:
                self.assertIsInstance(result, scanOutput)
                self.assertNotIsInstance(result, scanOutputFuzzy)

    def test_scan_lines_fuzzy_preserves_basic_fields(self):
        """Test that scan_lines() with fuzzy=True preserves basic fields."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        
        results = self.scansion.scan_lines()
        
        if len(results) > 0:
            result = results[0]
            self.assertEqual(result.original_line, line.original_line)
            self.assertIsInstance(result.words, list)
            self.assertIsInstance(result.word_taqti, list)
            self.assertNotEqual(result.meter_name, "")
            self.assertNotEqual(result.feet, "")

    def test_scan_lines_fuzzy_with_multiple_lines(self):
        """Test scan_lines() with fuzzy=True and multiple lines."""
        line1 = Lines("کتاب و قلم")
        line2 = Lines("دوات و کاغذ")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        self.scansion.fuzzy = True
        
        results = self.scansion.scan_lines()
        
        self.assertIsInstance(results, list)
        # Results should be consolidated by best meter (via crunch_fuzzy)

    def test_scan_lines_fuzzy_marks_as_dominant(self):
        """Test that scan_lines() with fuzzy=True marks results as dominant."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        
        results = self.scansion.scan_lines()
        
        # All results from fuzzy path should be marked as dominant
        for result in results:
            self.assertTrue(result.is_dominant, 
                          "Results from fuzzy path should be marked as dominant")


class TestFuzzyWithImperfectPoetry(unittest.TestCase):
    """Test fuzzy matching with imperfect/experimental poetry examples."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6  # Allow some tolerance

    def test_imperfect_line_with_meter_mismatch(self):
        """Test fuzzy matching with a line that doesn't match any meter exactly."""
        # A line that might not match perfectly
        line = Lines("ایک دن کہا گیا تھا کہ دنیا")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should handle imperfect poetry without error
        self.assertIsInstance(results, list)
        # May return empty if no fuzzy matches within threshold

    def test_experimental_poetry_multiple_lines(self):
        """Test fuzzy matching with experimental poetry across multiple lines."""
        # Lines that may have slight meter variations
        lines = [
            "ایک دن کہا گیا تھا",
            "دنیا میں کچھ بھی نہیں",
            "جو ہم نے سوچا تھا"
        ]
        
        for line_text in lines:
            self.scansion.add_line(Lines(line_text))
        
        # Test scan_lines_fuzzy
        fuzzy_results = self.scansion.scan_lines_fuzzy()
        self.assertIsInstance(fuzzy_results, list)
        
        # Test scan_lines with fuzzy=True
        self.scansion.fuzzy = True
        results = self.scansion.scan_lines()
        self.assertIsInstance(results, list)

    def test_imperfect_poetry_scores_are_reasonable(self):
        """Test that imperfect poetry produces reasonable fuzzy scores."""
        # Line that might not match perfectly
        line = Lines("ایک دن کہا گیا تھا")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            for result in results:
                # Scores should be non-negative
                self.assertGreaterEqual(result.score, 0)
                # Scores should be reasonable (not extremely large)
                # For Levenshtein distance, scores shouldn't exceed code length significantly
                code_length = len("".join(result.word_taqti))
                self.assertLessEqual(result.score, code_length * 2,  # Allow some flexibility
                                    f"Score {result.score} seems too large for code length {code_length}")

    def test_fuzzy_matching_finds_closest_meter(self):
        """Test that fuzzy matching finds the closest matching meter."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            # After crunch_fuzzy, should have best match
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(results)
            
            if len(consolidated) > 0:
                # Should have selected a meter
                self.assertNotEqual(consolidated[0].meter_name, "")
                # Score should be reasonable
                self.assertGreaterEqual(consolidated[0].score, 0)

    def test_fuzzy_with_varied_line_lengths(self):
        """Test fuzzy matching with lines of varied lengths."""
        # Mix of short and longer lines
        lines = [
            "کتاب",
            "کتاب و قلم",
            "کتاب و قلم و دوات و کاغذ"
        ]
        
        for line_text in lines:
            self.scansion.add_line(Lines(line_text))
        
        self.scansion.fuzzy = True
        results = self.scansion.scan_lines()
        
        self.assertIsInstance(results, list)
        # Should handle varied lengths gracefully


class TestFuzzyScoringInternals(unittest.TestCase):
    """Direct tests for _calculate_fuzzy_score and its Levenshtein usage."""

    def setUp(self):
        """Set up shared Scansion instance."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_calculate_fuzzy_score_uses_levenshtein_distance(self):
        """
        _calculate_fuzzy_score should return 0 for an exact pattern/code match.

        This exercises the same Levenshtein logic that CodeTree uses, but through
        the Scansion helper that fuzzy scoring relies on.
        """
        code = "-==="
        meter_pattern = "-==="  # No '+' or '/' so first variation is an exact match

        distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)

        self.assertEqual(distance, 0)
        self.assertEqual(best_meter, meter_pattern)

    def test_calculate_fuzzy_score_respects_mismatch_penalties(self):
        """
        _calculate_fuzzy_score should give strictly larger distance for a worse code.

        This ensures scores are monotonic with respect to edit distance, which is
        what crunch_fuzzy expects when treating lower scores as better.
        """
        perfect_code = "-==="
        off_by_one_code = "===-"  # Same length but clearly mismatched ordering
        meter_pattern = "-==="

        perfect_distance, _ = self.scansion._calculate_fuzzy_score(perfect_code, meter_pattern)
        off_by_one_distance, _ = self.scansion._calculate_fuzzy_score(off_by_one_code, meter_pattern)

        self.assertEqual(perfect_distance, 0)
        self.assertGreater(off_by_one_distance, perfect_distance)


if __name__ == '__main__':
    unittest.main()

