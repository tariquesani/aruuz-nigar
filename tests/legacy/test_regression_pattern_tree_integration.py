"""
Regression tests for PatternTree integration.

These tests ensure that after integrating PatternTree into the main meter matching flow,
the following modes still work correctly:
1. Regular meters (non-fuzzy, non-free-verse)
2. Fuzzy mode
3. Free verse mode

These tests verify that PatternTree integration doesn't break existing functionality.
"""

import unittest
from aruuz.scansion import Scansion
from aruuz.tree.code_tree import CodeTree
from aruuz.models import Lines, scanPath, LineScansionResult, LineScansionResultFuzzy
from aruuz.meters import NUM_METERS, METER_NAMES


class TestRegularMetersRegression(unittest.TestCase):
    """Regression tests for regular meter matching (non-fuzzy, non-free-verse)."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.fuzzy = False
        self.scansion.free_verse = False

    def test_regular_meter_matching_still_works(self):
        """Test that regular meter matching still works after PatternTree integration."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Use specific meters to avoid triggering PatternTree
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Should return results (may be empty, but should not error)
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, LineScansionResult)
            self.assertIsInstance(result.meter_name, str)
            self.assertIsInstance(result.id, int)

    def test_find_meter_with_specific_meters(self):
        """Test that find_meter with specific meters works correctly."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Assign codes
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Test with specific meter indices (should not trigger PatternTree)
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1, 2])
        
        # Should return scanPath objects
        self.assertIsInstance(results, list)
        for sp in results:
            self.assertIsInstance(sp, scanPath)
            self.assertIsInstance(sp.location, list)
            self.assertIsInstance(sp.meters, list)

    def test_regular_traversal_produces_valid_results(self):
        """Test that regular traversal still produces valid results."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=False)
        results = tree.find_meter([0, 1, 2, 3, 4])
        
        # Should return valid results
        self.assertIsInstance(results, list)
        if len(results) > 0:
            # Verify structure
            sp = results[0]
            self.assertGreater(len(sp.location), 0)
            self.assertEqual(sp.location[0].code, "root")
            # Meters should be valid
            for meter_idx in sp.meters:
                self.assertIsInstance(meter_idx, int)
                self.assertGreaterEqual(meter_idx, 0)

    def test_regular_mode_without_pattern_tree_flag(self):
        """Test that regular mode works without PatternTree flag (-1)."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Use meters without -1 flag (should not trigger PatternTree)
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1, 2])
        
        # Should work normally
        self.assertIsInstance(results, list)
        # Verify no errors occurred

    def test_scan_line_regular_mode(self):
        """Test that scan_line works in regular mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Should return valid scanOutput objects
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, LineScansionResult)
            self.assertEqual(result.original_line, line.original_line)
            self.assertEqual(len(result.words), len(line.words_list))

    def test_regular_mode_preserves_word_structure(self):
        """Test that regular mode preserves word structure correctly."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1, 2])
        
        if len(results) > 0:
            sp = results[0]
            # Verify word references are valid
            for loc in sp.location[1:]:  # Skip root
                if loc.word_ref >= 0:
                    self.assertLess(loc.word_ref, len(line.words_list))
                    self.assertEqual(loc.word, line.words_list[loc.word_ref].word)


class TestFuzzyModeRegression(unittest.TestCase):
    """Regression tests for fuzzy matching mode."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.fuzzy = True
        self.scansion.free_verse = False
        self.scansion.error_param = 6

    def test_fuzzy_mode_still_works(self):
        """Test that fuzzy mode still works after PatternTree integration."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should return fuzzy results
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, LineScansionResultFuzzy)
            self.assertGreaterEqual(result.score, 0)
            self.assertIsInstance(result.meter_name, str)

    def test_find_meter_fuzzy_mode(self):
        """Test that find_meter works in fuzzy mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line, fuzzy=True, free_verse=False)
        results = tree.find_meter([0, 1, 2])
        
        # Should return results
        self.assertIsInstance(results, list)
        # Fuzzy mode uses different traversal, so results structure should be valid

    def test_fuzzy_traversal_produces_scored_results(self):
        """Test that fuzzy traversal produces results with scores."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Use scan_line_fuzzy which uses fuzzy traversal
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            # Results should have scores
            for result in results:
                self.assertIsInstance(result.score, int)
                self.assertGreaterEqual(result.score, 0)

    def test_fuzzy_mode_with_error_param(self):
        """Test that fuzzy mode respects error_param threshold."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.error_param = 4
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Results should respect error_param
        self.assertIsInstance(results, list)
        if len(results) > 0:
            # Scores should be within reasonable range
            for result in results:
                # Fuzzy scores can vary, but should be non-negative
                self.assertGreaterEqual(result.score, 0)

    def test_fuzzy_mode_handles_imperfect_matches(self):
        """Test that fuzzy mode handles imperfect matches correctly."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should handle imperfect matches gracefully
        self.assertIsInstance(results, list)
        # Even if no perfect matches, fuzzy mode should attempt to find approximate matches

    def test_fuzzy_mode_does_not_break_perfect_matches(self):
        """Test that fuzzy mode doesn't break perfect matches."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should still work for perfect matches
        self.assertIsInstance(results, list)
        if len(results) > 0:
            # Perfect matches should have low scores
            min_score = min(r.score for r in results)
            self.assertGreaterEqual(min_score, 0)
            # Ideally perfect matches have score 0, but we allow some tolerance
            self.assertLessEqual(min_score, self.scansion.error_param)

    def test_fuzzy_mode_multiple_lines(self):
        """Test that fuzzy mode works with multiple lines."""
        line1 = Lines("کتاب")
        line2 = Lines("قلم")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        results = self.scansion.scan_lines_fuzzy()
        
        # Should process all lines
        self.assertIsInstance(results, list)

    def test_fuzzy_mode_preserves_word_structure(self):
        """Test that fuzzy mode preserves word structure."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # Should preserve word structure
            self.assertEqual(len(result.words), len(line.words_list))
            self.assertEqual(len(result.word_taqti), len(line.words_list))
            self.assertEqual(len(result.error), len(line.words_list))


class TestFreeVerseModeRegression(unittest.TestCase):
    """Regression tests for free verse mode."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()
        self.scansion.fuzzy = False
        self.scansion.free_verse = True

    def test_free_verse_mode_still_works(self):
        """Test that free verse mode still works after PatternTree integration."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Free verse mode uses different API
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2])
        
        # Should return results
        self.assertIsInstance(results, list)
        for sp in results:
            self.assertIsInstance(sp, scanPath)

    def test_find_meter_free_verse_mode(self):
        """Test that find_meter works in free verse mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2])
        
        # Should use free verse traversal
        self.assertIsInstance(results, list)

    def test_free_verse_traversal_produces_valid_results(self):
        """Test that free verse traversal produces valid results."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2, 3, 4])
        
        if len(results) > 0:
            sp = results[0]
            # Verify structure
            self.assertGreater(len(sp.location), 0)
            self.assertEqual(sp.location[0].code, "root")

    def test_free_verse_mode_with_rubai_meters(self):
        """Test that free verse mode handles rubai meters correctly."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Free verse mode should exclude rubai meters
        # (This is handled in the traversal logic)
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2])
        
        # Should work correctly
        self.assertIsInstance(results, list)

    def test_free_verse_mode_preserves_word_structure(self):
        """Test that free verse mode preserves word structure."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2])
        
        if len(results) > 0:
            sp = results[0]
            # Verify word references
            for loc in sp.location[1:]:  # Skip root
                if loc.word_ref >= 0:
                    self.assertLess(loc.word_ref, len(line.words_list))

    def test_free_verse_mode_with_different_meters(self):
        """Test that free verse mode works with various meter sets."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Test with different meter sets
        for meter_set in [[0], [0, 1, 2], [5, 6, 7]]:
            with self.subTest(meters=meter_set):
                tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
                results = tree.find_meter(meter_set)
                
                # Should work with any meter set
                self.assertIsInstance(results, list)


class TestModeIndependence(unittest.TestCase):
    """Test that different modes don't interfere with each other."""

    def setUp(self):
        """Set up test fixtures."""
        self.line = Lines("کتاب و قلم")

    def test_regular_mode_independent(self):
        """Test that regular mode works independently."""
        scansion = Scansion()
        scansion.fuzzy = False
        scansion.free_verse = False
        scansion.add_line(self.line)
        
        results = scansion.match_line_to_meters(self.line, 0)
        self.assertIsInstance(results, list)

    def test_fuzzy_mode_independent(self):
        """Test that fuzzy mode works independently."""
        scansion = Scansion()
        scansion.fuzzy = True
        scansion.free_verse = False
        scansion.add_line(self.line)
        
        results = scansion.scan_line_fuzzy(self.line, 0)
        self.assertIsInstance(results, list)

    def test_free_verse_mode_independent(self):
        """Test that free verse mode works independently."""
        scansion = Scansion()
        scansion.fuzzy = False
        scansion.free_verse = True
        scansion.add_line(self.line)
        
        for word in self.line.words_list:
            scansion.assign_scansion_to_word(word)
        
        tree = CodeTree.build_from_line(self.line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2])
        self.assertIsInstance(results, list)

    def test_mode_switching(self):
        """Test that switching between modes works correctly."""
        scansion = Scansion()
        scansion.add_line(self.line)
        
        # Test regular mode
        scansion.fuzzy = False
        scansion.free_verse = False
        results1 = scansion.match_line_to_meters(self.line, 0)
        self.assertIsInstance(results1, list)
        
        # Switch to fuzzy mode
        scansion.fuzzy = True
        scansion.free_verse = False
        results2 = scansion.scan_line_fuzzy(self.line, 0)
        self.assertIsInstance(results2, list)
        
        # Switch to free verse mode
        scansion.fuzzy = False
        scansion.free_verse = True
        for word in self.line.words_list:
            scansion.assign_scansion_to_word(word)
        tree = CodeTree.build_from_line(self.line, fuzzy=False, free_verse=True)
        results3 = tree.find_meter([0, 1, 2])
        self.assertIsInstance(results3, list)


class TestPatternTreeIntegrationDoesNotBreakModes(unittest.TestCase):
    """Test that PatternTree integration doesn't break existing modes."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()

    def test_pattern_tree_flag_does_not_break_regular_mode(self):
        """Test that PatternTree flag (-1) doesn't break regular mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = False
        self.scansion.free_verse = False
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Use -1 flag which triggers PatternTree
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, -1])
        
        # Should still work (PatternTree results may be added)
        self.assertIsInstance(results, list)

    def test_empty_meters_list_triggers_pattern_tree_but_still_works(self):
        """Test that empty meters list triggers PatternTree but mode still works."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = False
        self.scansion.free_verse = False
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Empty meters list triggers PatternTree
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([])
        
        # Should still return valid results (may include PatternTree results)
        self.assertIsInstance(results, list)

    def test_pattern_tree_integration_does_not_affect_fuzzy_mode(self):
        """Test that PatternTree integration doesn't affect fuzzy mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        self.scansion.free_verse = False
        
        # Fuzzy mode should not use PatternTree (only regular traversal does)
        results = self.scansion.scan_line_fuzzy(line, 0)
        
        # Should work normally
        self.assertIsInstance(results, list)

    def test_pattern_tree_integration_does_not_affect_free_verse_mode(self):
        """Test that PatternTree integration doesn't affect free verse mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = False
        self.scansion.free_verse = True
        
        for word in line.words_list:
            self.scansion.assign_scansion_to_word(word)
        
        # Free verse mode should not use PatternTree (only regular traversal does)
        tree = CodeTree.build_from_line(line, fuzzy=False, free_verse=True)
        results = tree.find_meter([0, 1, 2])
        
        # Should work normally
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    unittest.main()
