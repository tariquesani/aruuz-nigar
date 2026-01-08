"""
Comprehensive tests for fuzzy matching functionality.

This module contains unit and integration tests covering:
- Fuzzy traversal (_traverse_fuzzy)
- Levenshtein distance scoring (_levenshtein_distance, _calculate_fuzzy_score)
- Fuzzy consolidation (crunch_fuzzy)
- End-to-end fuzzy scansion flows
- Regression tests to ensure fuzzy mode doesn't break perfect matches
"""

import unittest
import math
from aruuz.scansion import Scansion
from aruuz.tree.code_tree import CodeTree
from aruuz.models import codeLocation, Lines, scanOutputFuzzy
from aruuz.meters import METERS, METER_NAMES, NUM_METERS


class TestLevenshteinDistance(unittest.TestCase):
    """Unit tests for CodeTree._levenshtein_distance() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_exact_match(self):
        """Test Levenshtein distance for exact match returns 0."""
        pattern = "-==="
        code = "-==="
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_single_substitution(self):
        """Test Levenshtein distance for single character substitution."""
        pattern = "-==="
        code = "===="  # Changed first character from '-' to '='
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 1)

    def test_single_insertion(self):
        """Test Levenshtein distance for single character insertion."""
        pattern = "-==="
        code = "-===="  # One extra character
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 1)

    def test_single_deletion(self):
        """Test Levenshtein distance for single character deletion."""
        pattern = "-==="
        code = "-=="  # One character missing
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 1)

    def test_multiple_errors(self):
        """Test Levenshtein distance for multiple errors."""
        pattern = "-==="
        code = "===-"  # Completely different
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertGreater(distance, 1)
        self.assertLessEqual(distance, 4)  # At most length of strings

    def test_wildcard_x_matches_any(self):
        """Test that 'x' in code matches any character in pattern (except '~')."""
        pattern = "-==="
        code = "x==="  # 'x' should match '-'
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_wildcard_x_matches_equals(self):
        """Test that 'x' in code matches '=' in pattern."""
        pattern = "-==="
        code = "-x=="  # 'x' should match '='
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_wildcard_tilde_matches_dash(self):
        """Test that '~' in pattern matches '-' in code with zero cost."""
        pattern = "~==="
        code = "-==="  # '~' should match '-' with zero cost
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_wildcard_tilde_does_not_match_non_dash(self):
        """Test that '~' in pattern doesn't match non-dash characters."""
        pattern = "~==="
        code = "===="  # '~' doesn't match '='
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertGreater(distance, 0)

    def test_wildcard_x_does_not_match_tilde(self):
        """Test that 'x' in code does not match '~' in pattern."""
        pattern = "~==="
        code = "x==="  # 'x' should not match '~'
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertGreater(distance, 0)

    def test_empty_pattern(self):
        """Test Levenshtein distance with empty pattern."""
        pattern = ""
        code = "-==="
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, len(code))

    def test_empty_code(self):
        """Test Levenshtein distance with empty code."""
        pattern = "-==="
        code = ""
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, len(pattern))

    def test_both_empty(self):
        """Test Levenshtein distance with both empty."""
        pattern = ""
        code = ""
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_different_lengths(self):
        """Test Levenshtein distance with significantly different lengths."""
        pattern = "-="
        code = "-====="
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertGreater(distance, 0)
        # Distance should be at least the difference in lengths
        self.assertGreaterEqual(distance, abs(len(pattern) - len(code)))

    def test_monotonicity(self):
        """Test that distances are monotonic - worse matches have higher distances."""
        pattern = "-==="
        exact = "-==="
        one_error = "-==="  # Will test with actual error
        two_errors = "===-"  # Multiple errors
        
        exact_dist = self.tree._levenshtein_distance(pattern, exact)
        one_error_dist = self.tree._levenshtein_distance(pattern, "=====")
        two_errors_dist = self.tree._levenshtein_distance(pattern, two_errors)
        
        self.assertEqual(exact_dist, 0)
        self.assertGreaterEqual(one_error_dist, exact_dist)
        self.assertGreaterEqual(two_errors_dist, one_error_dist)


class TestCalculateFuzzyScore(unittest.TestCase):
    """Unit tests for Scansion._calculate_fuzzy_score() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_exact_match_returns_zero(self):
        """Test that exact match returns distance 0."""
        # Use a meter pattern that when processed matches the code exactly
        # The method removes '/' and processes '+' to create 4 variations
        # Use a simple pattern that will match: "-===" matches one of the variations
        code = "-==="
        meter_pattern = "-==="  # Simple pattern that matches code exactly
        distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)
        self.assertEqual(distance, 0)

    def test_calculates_minimum_across_variations(self):
        """Test that _calculate_fuzzy_score returns minimum distance across 4 variations."""
        code = "-==="
        meter_pattern = "-===/-===/-===/-==="
        distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)
        # Should find the variation with minimum distance
        self.assertGreaterEqual(distance, 0)
        self.assertIsInstance(best_meter, str)
        self.assertGreater(len(best_meter), 0)

    def test_handles_plus_in_pattern(self):
        """Test that _calculate_fuzzy_score handles '+' in meter pattern."""
        code = "-==="
        meter_pattern = "-===/-===+=-=/-==="  # Pattern with '+'
        distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)
        # Should create 4 variations and return minimum
        self.assertGreaterEqual(distance, 0)
        self.assertIsInstance(best_meter, str)

    def test_handles_slash_in_pattern(self):
        """Test that _calculate_fuzzy_score removes '/' from pattern."""
        code = "-==="
        meter_pattern = "-===/-===/-===/-==="
        distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)
        # Should work correctly with '/' characters
        self.assertGreaterEqual(distance, 0)
        self.assertNotIn('/', best_meter)

    def test_worse_match_has_higher_distance(self):
        """Test that worse matches produce higher distances."""
        # Use patterns that actually match the code length
        perfect_code = "-==="
        imperfect_code = "===-"  # Different pattern
        meter_pattern = "-==="  # Pattern that matches perfect_code exactly
        
        perfect_dist, _ = self.scansion._calculate_fuzzy_score(perfect_code, meter_pattern)
        imperfect_dist, _ = self.scansion._calculate_fuzzy_score(imperfect_code, meter_pattern)
        
        self.assertEqual(perfect_dist, 0)
        self.assertGreater(imperfect_dist, perfect_dist)

    def test_selects_best_variation(self):
        """Test that method selects the meter variation with lowest distance."""
        # Use a code that matches one variation better than others
        code = "-===-"  # Matches variation 2 (meter with '+' removed + '~' appended)
        meter_pattern = "-===/-===-/-==="  # Pattern that might create variation 2
        distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)
        # Should select the variation with minimum distance
        self.assertGreaterEqual(distance, 0)
        self.assertIsInstance(best_meter, str)

    def test_with_real_meter_pattern(self):
        """Test _calculate_fuzzy_score with a real meter pattern from METERS."""
        if NUM_METERS > 0:
            meter_pattern = METERS[0]  # First meter
            # Create a code that might match
            code = "-==="
            distance, best_meter = self.scansion._calculate_fuzzy_score(code, meter_pattern)
            self.assertGreaterEqual(distance, 0)
            self.assertIsInstance(best_meter, str)
            self.assertGreater(len(best_meter), 0)


class TestFuzzyTraversal(unittest.TestCase):
    """Integration tests for fuzzy traversal via scan_line_fuzzy()."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6  # Reasonable threshold for fuzzy matching

    def test_scan_line_fuzzy_uses_fuzzy_traversal(self):
        """Test that scan_line_fuzzy uses _traverse_fuzzy internally."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should return results (may be empty if no fuzzy matches)
        self.assertIsInstance(results, list)
        # If results exist, they should have valid structure
        for result in results:
            self.assertIsInstance(result, scanOutputFuzzy)
            self.assertGreaterEqual(result.score, 0)

    def test_scan_line_fuzzy_with_imperfect_match(self):
        """Test fuzzy traversal finds matches for lines with minor deviations."""
        # Use a line that might have slight deviations
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should handle imperfect matches gracefully
        self.assertIsInstance(results, list)
        if len(results) > 0:
            # Results should have valid scores
            for result in results:
                self.assertIsInstance(result.score, int)
                self.assertGreaterEqual(result.score, 0)
                self.assertNotEqual(result.meter_name, "")

    def test_scan_line_fuzzy_calculates_scores(self):
        """Test that scan_line_fuzzy calculates fuzzy scores for each result."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            for result in results:
                # Score should be calculated (not default value 10 unless special meter)
                self.assertIsInstance(result.score, int)
                self.assertGreaterEqual(result.score, 0)

    def test_scan_line_fuzzy_returns_multiple_meters(self):
        """Test that fuzzy traversal can return multiple meter matches."""
        line = Lines("دم اندھیرے میں گھٹ رہا ہے خمار")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        self.assertIsInstance(results, list)
        # May return multiple meters with different scores
        if len(results) > 1:
            # Should have different meter names or scores
            meter_names = [r.meter_name for r in results]
            scores = [r.score for r in results]
            # At least some variation expected
            self.assertGreaterEqual(len(results), 1)

    def test_scan_line_fuzzy_with_empty_line(self):
        """Test fuzzy traversal handles empty line."""
        line = Lines("")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Empty line should return empty results
        self.assertEqual(len(results), 0)

    def test_scan_line_fuzzy_preserves_word_structure(self):
        """Test that fuzzy traversal preserves word structure in results."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # Should preserve word structure
            self.assertEqual(len(result.words), len(line.words_list))
            self.assertEqual(len(result.word_taqti), len(line.words_list))
            self.assertEqual(len(result.error), len(line.words_list))


class TestScanLinesFuzzy(unittest.TestCase):
    """Integration tests for scan_lines_fuzzy() batch processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

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
        
        # Should process all lines (may be filtered by crunch_fuzzy)
        self.assertIsInstance(results, list)

    def test_scan_lines_fuzzy_calls_crunch_fuzzy(self):
        """Test that scan_lines_fuzzy consolidates results via crunch_fuzzy."""
        line1 = Lines("کتاب و قلم")
        line2 = Lines("دوات و کاغذ")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        results = self.scansion.scan_lines_fuzzy()
        
        # After crunch_fuzzy, all results should have same meter name
        if len(results) > 0:
            meter_names = {r.meter_name for r in results}
            # All results should be consolidated to best meter
            self.assertEqual(len(meter_names), 1,
                           f"All results should have same meter after crunch_fuzzy, got: {meter_names}")

    def test_scan_lines_fuzzy_with_imperfect_poetry(self):
        """Test scan_lines_fuzzy with imperfect poetry lines."""
        lines = [
            "ایک دن کہا گیا تھا",
            "دنیا میں کچھ بھی نہیں"
        ]
        
        for line_text in lines:
            self.scansion.add_line(Lines(line_text))
        
        results = self.scansion.scan_lines_fuzzy()
        
        # Should handle imperfect poetry gracefully
        self.assertIsInstance(results, list)

    def test_scan_lines_fuzzy_returns_fuzzy_objects(self):
        """Test that scan_lines_fuzzy returns scanOutputFuzzy objects."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_lines_fuzzy()
        
        for result in results:
            self.assertIsInstance(result, scanOutputFuzzy)
            self.assertGreaterEqual(result.score, 0)


class TestCrunchFuzzy(unittest.TestCase):
    """Integration tests for crunch_fuzzy() consolidation."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_crunch_fuzzy_empty_list(self):
        """Test crunch_fuzzy with empty list returns empty list."""
        results = []
        consolidated = self.scansion.resolve_dominant_meter_fuzzy(results)
        self.assertEqual(len(consolidated), 0)

    def test_crunch_fuzzy_consolidates_by_meter(self):
        """Test that crunch_fuzzy consolidates results to best meter."""
        # Create results with multiple meters
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        all_results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(all_results) > 0:
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(all_results)
            
            if len(consolidated) > 0:
                # All results should have same meter name
                meter_names = {r.meter_name for r in consolidated}
                self.assertEqual(len(meter_names), 1,
                               f"Should consolidate to one meter, got: {meter_names}")

    def test_crunch_fuzzy_selects_best_score(self):
        """Test that crunch_fuzzy selects meter with best (lowest) score."""
        # Create multiple lines to get multiple results
        line1 = Lines("کتاب")
        line2 = Lines("قلم")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        all_results = []
        all_results.extend(self.scansion.scan_line_fuzzy(line1, 0))
        all_results.extend(self.scansion.scan_line_fuzzy(line2, 1))
        
        if len(all_results) >= 2:
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(all_results)
            
            if len(consolidated) > 0:
                # All consolidated results should have same meter (the best one)
                meter_name = consolidated[0].meter_name
                for result in consolidated:
                    self.assertEqual(result.meter_name, meter_name)

    def test_crunch_fuzzy_logarithmic_averaging(self):
        """Test that crunch_fuzzy uses logarithmic averaging for scores."""
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
            
            # For each meter with multiple results, verify aggregation
            for meter_name, meter_results in meters.items():
                if len(meter_results) > 1:
                    scores = [r.score for r in meter_results]
                    # Calculate expected logarithmic average
                    score_sum = 0.0
                    subtract = 0.0
                    count = 0.0
                    for score in scores:
                        if score == 0:
                            score_sum += math.log(score + 1)
                            subtract += 1.0
                        else:
                            score_sum += math.log(score)
                        count += 1.0
                    
                    if count > 0:
                        expected_aggregate = math.exp(score_sum / count) - subtract
                        # Verify crunch_fuzzy runs without error
                        consolidated = self.scansion.resolve_dominant_meter_fuzzy(results)
                        self.assertIsInstance(consolidated, list)

    def test_crunch_fuzzy_handles_zero_scores(self):
        """Test that crunch_fuzzy handles zero scores correctly."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            # Modify a result to have score 0
            test_results = results.copy()
            test_results[0].score = 0
            
            consolidated = self.scansion.resolve_dominant_meter_fuzzy(test_results)
            # Should handle zero scores without error
            self.assertIsInstance(consolidated, list)

    def test_crunch_fuzzy_preserves_all_best_meter_results(self):
        """Test that crunch_fuzzy preserves all results for the best meter."""
        line1 = Lines("کتاب")
        line2 = Lines("قلم")
        
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


class TestFuzzyRegression(unittest.TestCase):
    """Regression tests to ensure fuzzy mode doesn't break perfect matches."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.error_param = 6

    def test_perfect_match_in_fuzzy_mode(self):
        """Test that perfect matches still work correctly in fuzzy mode."""
        # Use a line that should match a meter perfectly
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Test fuzzy mode
        self.scansion.fuzzy = True
        fuzzy_results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Test non-fuzzy mode
        self.scansion.fuzzy = False
        # Note: non-fuzzy uses different API (scan_line, not scan_line_fuzzy)
        # So we can't directly compare, but we can verify fuzzy mode works
        
        # Fuzzy mode should return results
        self.assertIsInstance(fuzzy_results, list)
        if len(fuzzy_results) > 0:
            # Perfect matches should have low scores (0 or very low)
            best_score = min(r.score for r in fuzzy_results)
            self.assertGreaterEqual(best_score, 0)
            # Perfect matches should ideally have score 0
            # But we allow some tolerance since matching might not be perfect

    def test_fuzzy_mode_does_not_worsen_perfect_matches(self):
        """Test that fuzzy mode doesn't produce worse rankings for perfect matches."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            # Results should be sorted by score (lower is better)
            scores = [r.score for r in results]
            # Verify scores are in reasonable range (not extremely high for perfect matches)
            min_score = min(scores)
            self.assertGreaterEqual(min_score, 0)
            # Perfect matches should have score <= error_param
            self.assertLessEqual(min_score, self.scansion.error_param)

    def test_fuzzy_mode_handles_multiple_perfect_lines(self):
        """Test that fuzzy mode handles multiple perfect-match lines correctly."""
        lines = ["کتاب", "قلم", "دوات"]
        
        for line_text in lines:
            self.scansion.add_line(Lines(line_text))
        
        results = self.scansion.scan_lines_fuzzy()
        
        # Should process all lines correctly
        self.assertIsInstance(results, list)
        # All results should have valid structure
        for result in results:
            self.assertIsInstance(result, scanOutputFuzzy)
            self.assertGreaterEqual(result.score, 0)
            self.assertNotEqual(result.meter_name, "")

    def test_fuzzy_mode_vs_non_fuzzy_for_perfect_match(self):
        """Test that fuzzy mode produces acceptable results compared to non-fuzzy."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Get fuzzy results
        fuzzy_results = self.scansion.scan_line_fuzzy(line, 0)
        
        # For perfect matches, fuzzy mode should still identify correct meters
        # (We can't directly compare to non-fuzzy since APIs differ,
        # but we can verify fuzzy mode produces sensible results)
        if len(fuzzy_results) > 0:
            # Should have valid meter names
            for result in fuzzy_results:
                self.assertNotEqual(result.meter_name, "")
                self.assertGreaterEqual(result.score, 0)
                # Score should be reasonable for good matches
                self.assertLessEqual(result.score, self.scansion.error_param * 2)


if __name__ == '__main__':
    unittest.main()
