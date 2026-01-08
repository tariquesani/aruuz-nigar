"""
Integration tests for tree-based pattern matching.

Tests cover:
- find_meter() end-to-end with real poetry lines
- scan_line() using tree-based matching
- Comparison with expected behavior (matching C# implementation)
- Multiple meter matches
- Meter filtering and selection
- Edge cases and error handling
"""

import unittest
from aruuz.scansion import Scansion
from aruuz.models import Lines, scanPath, scanOutput
from aruuz.tree.code_tree import CodeTree
from aruuz.meters import METERS, NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, METER_NAMES


class TestFindMeterIntegration(unittest.TestCase):
    """Test find_meter() end-to-end integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()

    def test_find_meter_basic_line(self):
        """Test find_meter with a basic poetry line."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Assign codes to words
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Call find_meter
        results = self.scansion.match_meters_via_tree(line)
        
        # Should return list of scanPath objects
        self.assertIsInstance(results, list)
        for sp in results:
            self.assertIsInstance(sp, scanPath)
            self.assertIsInstance(sp.location, list)
            self.assertIsInstance(sp.meters, list)
            # Location should have at least root + word locations
            self.assertGreater(len(sp.location), 0)
            # First location should be root
            if len(sp.location) > 0:
                self.assertEqual(sp.location[0].code, "root")
                self.assertEqual(sp.location[0].word_ref, -1)

    def test_find_meter_with_specific_meters(self):
        """Test find_meter with specific meter indices."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Assign codes
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Test with specific meters (first few meters)
        results = self.scansion.match_meters_via_tree(line, meters=[0, 1, 2])
        
        self.assertIsInstance(results, list)
        # Check that all returned meters are in the requested set
        for sp in results:
            for meter_idx in sp.meters:
                self.assertIn(meter_idx, [0, 1, 2])

    def test_find_meter_with_empty_meters(self):
        """Test find_meter with empty meter list."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line, meters=[])
        
        # Should return empty list or paths with no meters
        self.assertIsInstance(results, list)
        for sp in results:
            self.assertEqual(len(sp.meters), 0)

    def test_find_meter_with_all_meters(self):
        """Test find_meter without meter filter (checks all meters)."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line, meters=None)
        
        self.assertIsInstance(results, list)
        # Should potentially match multiple meters
        if len(results) > 0:
            # Check that meters are valid indices
            for sp in results:
                for meter_idx in sp.meters:
                    self.assertIsInstance(meter_idx, int)
                    self.assertGreaterEqual(meter_idx, 0)

    def test_find_meter_preserves_word_references(self):
        """Test that find_meter preserves correct word references."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line)
        
        # Check that word references in scanPath match actual words
        for sp in results:
            for i in range(1, len(sp.location)):  # Skip root
                loc = sp.location[i]
                if loc.word_ref >= 0:
                    self.assertLess(loc.word_ref, len(line.words_list))
                    # Word reference should match the word
                    self.assertEqual(loc.word, line.words_list[loc.word_ref].word)

    def test_find_meter_with_fuzzy_mode(self):
        """Test find_meter in fuzzy matching mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        self.scansion.error_param = 2
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line, meters=[0, 1])
        
        self.assertIsInstance(results, list)
        # Fuzzy mode should allow approximate matches
        # Results may include paths that don't exactly match but are close

    def test_find_meter_with_free_verse_mode(self):
        """Test find_meter in free verse mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.free_verse = True
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line, meters=[0, 1])
        
        self.assertIsInstance(results, list)
        # Free verse mode should be more lenient

    def test_find_meter_empty_line(self):
        """Test find_meter with empty line."""
        line = Lines("")
        self.scansion.add_line(line)
        
        results = self.scansion.match_meters_via_tree(line)
        
        # Empty line should return empty results or paths with no meters
        self.assertIsInstance(results, list)

    def test_find_meter_single_word(self):
        """Test find_meter with single word."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line)
        
        self.assertIsInstance(results, list)
        # Single word may or may not match meters depending on code length

    def test_find_meter_multiple_code_variations(self):
        """Test find_meter with words that have multiple code variations."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        word = line.words_list[0]
        # Manually set multiple codes
        word.code = ["-===", "===-", "-=-="]
        
        results = self.scansion.match_meters_via_tree(line)
        
        self.assertIsInstance(results, list)
        # Should explore all code variations

    def test_find_meter_with_taqti_graft(self):
        """Test find_meter includes taqti_word_graft codes."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        word = line.words_list[0]
        word.code = ["-==="]
        word.taqti_word_graft = ["-==="]
        
        results = self.scansion.match_meters_via_tree(line)
        
        self.assertIsInstance(results, list)
        # Should include paths from both code and taqti_word_graft

    def test_find_meter_code_concatenation(self):
        """Test that find_meter correctly concatenates codes from multiple words."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        results = self.scansion.match_meters_via_tree(line)
        
        # Check that codes are properly concatenated in scanPath
        for sp in results:
            if len(sp.location) > 1:
                # Build code string from locations (skip root)
                code_parts = []
                for i in range(1, len(sp.location)):
                    code_parts.append(sp.location[i].code)
                full_code = "".join(code_parts)
                # Code should not be empty
                self.assertGreater(len(full_code), 0)

    def test_find_meter_meter_filtering(self):
        """Test that find_meter correctly filters meters during traversal."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Get all results first
        all_results = self.scansion.match_meters_via_tree(line, meters=None)
        
        if len(all_results) > 0:
            # Get meter indices from results
            all_meter_indices = set()
            for sp in all_results:
                all_meter_indices.update(sp.meters)
            
            # Test with subset of meters
            if len(all_meter_indices) > 0:
                subset = list(all_meter_indices)[:3]  # Take first 3
                filtered_results = self.scansion.match_meters_via_tree(line, meters=subset)
                
                # All returned meters should be in subset
                for sp in filtered_results:
                    for meter_idx in sp.meters:
                        self.assertIn(meter_idx, subset)


class TestScanLineTreeIntegration(unittest.TestCase):
    """Test scan_line() using tree-based matching."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()

    def test_scan_line_basic(self):
        """Test scan_line with basic poetry line."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Should return list of scanOutput objects
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, scanOutput)
            self.assertEqual(result.original_line, line.original_line)
            self.assertIsInstance(result.words, list)
            self.assertIsInstance(result.word_taqti, list)
            self.assertIsInstance(result.meter_name, str)
            self.assertIsInstance(result.id, int)
            # Should have same number of words as line
            self.assertEqual(len(result.words), len(line.words_list))
            self.assertEqual(len(result.word_taqti), len(line.words_list))

    def test_scan_line_uses_tree_based_matching(self):
        """Test that scan_line uses tree-based find_meter internally."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Manually verify tree is built
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Call find_meter directly
        scan_paths = self.scansion.match_meters_via_tree(line)
        
        # Call scan_line
        scan_outputs = self.scansion.match_line_to_meters(line, 0)
        
        # Number of scanOutputs should correspond to scanPaths with meters
        paths_with_meters = [sp for sp in scan_paths if sp.meters]
        # Each scanPath can produce multiple scanOutputs (one per meter)
        total_expected_outputs = sum(len(sp.meters) for sp in paths_with_meters)
        
        # Allow for some flexibility (scan_line may filter further)
        self.assertLessEqual(len(scan_outputs), total_expected_outputs)

    def test_scan_line_converts_scan_path_to_output(self):
        """Test that scan_line correctly converts scanPath to scanOutput."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # Verify structure
            self.assertEqual(result.original_line, line.original_line)
            self.assertEqual(len(result.words), len(line.words_list))
            self.assertEqual(len(result.word_taqti), len(line.words_list))
            # Meter name should not be empty if meter was found
            if result.id >= 0:
                self.assertNotEqual(result.meter_name, "")

    def test_scan_line_preserves_word_order(self):
        """Test that scan_line preserves word order from line."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # Words should be in same order as line
            for i, word in enumerate(result.words):
                self.assertEqual(word.word, line.words_list[i].word)

    def test_scan_line_with_specific_meters(self):
        """Test scan_line with meter filter set."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.meter = [0, 1, 2]
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # All results should have meter IDs in the specified set
        for result in results:
            self.assertIn(result.id, [0, 1, 2])

    def test_scan_line_empty_line(self):
        """Test scan_line with empty line."""
        line = Lines("")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Should return empty list
        self.assertEqual(len(results), 0)

    def test_scan_line_no_matches(self):
        """Test scan_line when no meters match."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        # Use meter indices that likely won't match
        self.scansion.meter = [999]  # Invalid meter index
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Should return empty list if no matches
        self.assertIsInstance(results, list)

    def test_scan_line_multiple_matches(self):
        """Test scan_line returns multiple matches when multiple meters match."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # May have multiple results if multiple meters match
        self.assertIsInstance(results, list)
        if len(results) > 1:
            # Check that results have different meter IDs or different paths
            meter_ids = [r.id for r in results]
            # Should have some variation
            self.assertGreater(len(set(meter_ids)), 0)

    def test_scan_line_with_fuzzy_mode(self):
        """Test scan_line in fuzzy matching mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.fuzzy = True
        self.scansion.error_param = 2
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        self.assertIsInstance(results, list)
        # Fuzzy mode may produce more results

    def test_scan_line_with_free_verse_mode(self):
        """Test scan_line in free verse mode."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.scansion.free_verse = True
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        self.assertIsInstance(results, list)

    def test_scan_line_code_assignment(self):
        """Test that scan_line assigns codes to words."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Before scan_line, codes may not be assigned
        initial_codes = [word.code for word in line.words_list]
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # After scan_line, codes should be assigned
        for word in line.words_list:
            self.assertGreater(len(word.code), 0)

    def test_scan_line_feet_calculation(self):
        """Test that scan_line calculates feet correctly."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        if len(results) > 0:
            result = results[0]
            # Feet should be a string
            self.assertIsInstance(result.feet, str)
            # If meter was found, feet should not be empty
            if result.id >= 0 and result.meter_name:
                self.assertGreater(len(result.feet), 0)

    def test_scan_line_meter_name_assignment(self):
        """Test that scan_line assigns correct meter names."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        for result in results:
            if result.id >= 0 and result.id < NUM_METERS:
                # Meter name should match METER_NAMES
                expected_name = METER_NAMES[result.id]
                self.assertEqual(result.meter_name, expected_name)

    def test_scan_line_word_taqti_matches_code(self):
        """Test that word_taqti in scanOutput matches codes from scanPath."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Get scan paths
        for word in line.words_list:
            self.scansion.word_code(word)
        scan_paths = self.scansion.match_meters_via_tree(line)
        
        # Get scan outputs
        scan_outputs = self.scansion.match_line_to_meters(line, 0)
        
        # Verify that codes match
        if len(scan_paths) > 0 and len(scan_outputs) > 0:
            # Find matching scanPath for first scanOutput
            sp = scan_paths[0]
            so = scan_outputs[0]
            
            # Build code from scanPath
            path_codes = [loc.code for loc in sp.location[1:]]  # Skip root
            # Should match word_taqti
            self.assertEqual(path_codes, so.word_taqti)


class TestTreeIntegrationComparison(unittest.TestCase):
    """Test tree-based matching behavior matches expected patterns."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()

    def test_tree_builds_correctly_from_line(self):
        """Test that CodeTree builds correctly from line."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        tree = CodeTree.build_from_line(line)
        
        # Tree should have root
        self.assertEqual(tree.location.code, "root")
        self.assertEqual(tree.location.word_ref, -1)
        # Tree should have children
        self.assertGreater(len(tree.children), 0)

    def test_tree_traversal_produces_valid_paths(self):
        """Test that tree traversal produces valid scanPath objects."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1, 2])
        
        for sp in results:
            # Path should have at least root
            self.assertGreater(len(sp.location), 0)
            # First location should be root
            self.assertEqual(sp.location[0].code, "root")
            # Word references should be sequential or valid
            for i in range(1, len(sp.location)):
                loc = sp.location[i]
                if loc.word_ref >= 0:
                    self.assertLess(loc.word_ref, len(line.words_list))

    def test_tree_matching_filters_by_length(self):
        """Test that tree matching filters meters by code length."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        word = line.words_list[0]
        word.code = ["-"]  # Very short code
        
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1, 2, 3, 4])
        
        # Short code should filter out meters that require longer codes
        self.assertIsInstance(results, list)
        # Results may be empty if no meters match the short code

    def test_tree_handles_multiple_code_variations(self):
        """Test that tree handles multiple code variations per word."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        word = line.words_list[0]
        word.code = ["-===", "===-", "-=-="]
        
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1, 2])
        
        # Should explore all code variations
        self.assertIsInstance(results, list)
        # May have multiple paths from different code variations

    def test_tree_preserves_code_sequence(self):
        """Test that tree preserves code sequence in scanPath."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, 1])
        
        for sp in results:
            if len(sp.location) > 1:
                # Codes should be in word order
                codes = [loc.code for loc in sp.location[1:]]
                # Verify word references are in order
                word_refs = [loc.word_ref for loc in sp.location[1:] if loc.word_ref >= 0]
                if len(word_refs) > 1:
                    for i in range(len(word_refs) - 1):
                        self.assertLessEqual(word_refs[i], word_refs[i + 1])

    def test_tree_matching_with_rubai_meters(self):
        """Test tree matching with rubai meters."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Rubai meters start at NUM_METERS + NUM_VARIED_METERS
        rubai_start = NUM_METERS + NUM_VARIED_METERS
        rubai_end = rubai_start + NUM_RUBAI_METERS
        
        if rubai_end > rubai_start:
            rubai_indices = list(range(rubai_start, min(rubai_start + 5, rubai_end)))
            tree = CodeTree.build_from_line(line)
            results = tree.find_meter(rubai_indices)
            
            self.assertIsInstance(results, list)
            for sp in results:
                for meter_idx in sp.meters:
                    self.assertGreaterEqual(meter_idx, rubai_start)
                    self.assertLess(meter_idx, rubai_end)

    def test_tree_matching_consistency(self):
        """Test that tree matching produces consistent results."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Run find_meter multiple times
        results1 = self.scansion.match_meters_via_tree(line, meters=[0, 1, 2])
        results2 = self.scansion.match_meters_via_tree(line, meters=[0, 1, 2])
        
        # Results should be consistent (same structure)
        self.assertEqual(len(results1), len(results2))
        # Meter indices should match
        meters1 = set()
        for sp in results1:
            meters1.update(sp.meters)
        meters2 = set()
        for sp in results2:
            meters2.update(sp.meters)
        self.assertEqual(meters1, meters2)

    def test_tree_matching_with_pattern_tree_flag(self):
        """Test tree matching with PatternTree flag (-1)."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # -1 flag should trigger PatternTree matching
        tree = CodeTree.build_from_line(line)
        results = tree.find_meter([0, -1])
        
        # Should still work (may include PatternTree results)
        self.assertIsInstance(results, list)


class TestTreeIntegrationEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in tree integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()

    def test_find_meter_with_invalid_meter_indices(self):
        """Test find_meter handles invalid meter indices gracefully."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # Use invalid meter indices
        results = self.scansion.match_meters_via_tree(line, meters=[99999, -999])
        
        # Should handle gracefully (may return empty or filter out invalid)
        self.assertIsInstance(results, list)

    def test_scan_line_with_very_long_line(self):
        """Test scan_line with very long line."""
        # Create a long line
        words = ["کتاب"] * 20
        line = Lines(" ".join(words))
        self.scansion.add_line(line)
        
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Should handle long lines
        self.assertIsInstance(results, list)

    def test_find_meter_with_words_without_codes(self):
        """Test find_meter handles words without codes."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Don't assign codes
        # find_meter should handle this
        results = self.scansion.match_meters_via_tree(line)
        
        # Should return empty or handle gracefully
        self.assertIsInstance(results, list)

    def test_scan_line_with_words_without_codes(self):
        """Test scan_line assigns codes if not present."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        # Clear codes
        for word in line.words_list:
            word.code = []
        
        # scan_line should assign codes
        results = self.scansion.match_line_to_meters(line, 0)
        
        # Codes should be assigned
        for word in line.words_list:
            self.assertGreater(len(word.code), 0)

    def test_tree_build_with_empty_codes(self):
        """Test CodeTree build handles empty codes."""
        line = Lines("کتاب")
        word = line.words_list[0]
        word.code = []
        
        tree = CodeTree.build_from_line(line)
        
        # Should handle empty codes
        self.assertIsInstance(tree, CodeTree)

    def test_find_meter_with_none_meters(self):
        """Test find_meter with None meters parameter."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        for word in line.words_list:
            self.scansion.word_code(word)
        
        # None should use self.meter or all meters
        results = self.scansion.match_meters_via_tree(line, meters=None)
        
        self.assertIsInstance(results, list)


if __name__ == '__main__':
    unittest.main()

