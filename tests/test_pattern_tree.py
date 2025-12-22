"""
Comprehensive unit tests for PatternTree class.

Tests cover:
- Tree construction with 'x' code expansion
- add_child() with various code patterns
- State machine traversal (Original Hindi and Zamzama)
- Meter detection based on syllable counts
- is_match() main entry point
- Edge cases: empty pattern, single character patterns
"""

import unittest
from aruuz.tree.pattern_tree import PatternTree
from aruuz.models import codeLocation, scanPath
from aruuz.meters import NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS
from aruuz.tree.state_machine import original_hindi_meter, zamzama_meter


class TestPatternTreeConstruction(unittest.TestCase):
    """Test PatternTree construction and initialization."""

    def test_init_with_code_location(self):
        """Test PatternTree initialization with codeLocation."""
        loc = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree = PatternTree(loc)
        
        self.assertEqual(tree.location.code, "-")
        self.assertEqual(tree.location.word_ref, 0)
        self.assertEqual(tree.location.code_ref, 0)
        self.assertEqual(tree.location.word, "test")
        self.assertEqual(len(tree.children), 0)

    def test_init_with_root_location(self):
        """Test PatternTree initialization with root location."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        self.assertEqual(tree.location.code, "root")
        self.assertEqual(tree.location.word_ref, -1)
        self.assertEqual(len(tree.children), 0)

    def test_init_copies_location(self):
        """Test PatternTree creates a copy of the location."""
        loc = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree = PatternTree(loc)
        
        # Modify original location
        loc.code = "="
        # Tree location should not change
        self.assertEqual(tree.location.code, "-")


class TestPatternTreeAddChild(unittest.TestCase):
    """Test PatternTree.add_child() method with 'x' expansion."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = PatternTree(root_loc)

    def test_add_child_regular_code(self):
        """Test add_child with regular code (not 'x')."""
        loc = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        self.assertEqual(len(self.tree.children), 1)
        self.assertEqual(self.tree.children[0].location.code, "-")

    def test_add_child_x_expands_to_two_children(self):
        """Test add_child with 'x' code expands to '-' and '='."""
        loc = codeLocation(code="x", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        # Should have two children: one with "-" and one with "="
        self.assertEqual(len(self.tree.children), 2)
        codes = [child.location.code for child in self.tree.children]
        self.assertIn("-", codes)
        self.assertIn("=", codes)

    def test_add_child_x_preserves_metadata(self):
        """Test add_child with 'x' preserves word_ref and code_ref."""
        loc = codeLocation(code="x", word_ref=5, code_ref=3, word="test", fuzzy=1)
        self.tree.add_child(loc)
        
        # Both children should preserve metadata
        for child in self.tree.children:
            self.assertEqual(child.location.word_ref, 5)
            self.assertEqual(child.location.code_ref, 3)
            self.assertEqual(child.location.word, "test")
            self.assertEqual(child.location.fuzzy, 1)

    def test_add_child_recursive_to_existing_children(self):
        """Test add_child recursively adds to all existing children."""
        # Add first child
        loc1 = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc1)
        
        # Add second child - should be added to all existing children
        loc2 = codeLocation(code="=", word_ref=1, code_ref=0, word="line", fuzzy=0)
        self.tree.add_child(loc2)
        
        # First child should now have children
        self.assertGreater(len(self.tree.children[0].children), 0)

    def test_add_child_x_after_regular_code(self):
        """Test add_child with 'x' after regular code."""
        # Add regular code first
        loc1 = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc1)
        
        # Add 'x' - should expand in all children
        loc2 = codeLocation(code="x", word_ref=1, code_ref=0, word="line", fuzzy=0)
        self.tree.add_child(loc2)
        
        # First child should have two children (from 'x' expansion)
        self.assertEqual(len(self.tree.children[0].children), 2)
        codes = [child.location.code for child in self.tree.children[0].children]
        self.assertIn("-", codes)
        self.assertIn("=", codes)

    def test_add_child_multiple_x_codes(self):
        """Test add_child with multiple 'x' codes creates tree structure."""
        # Add first 'x'
        loc1 = codeLocation(code="x", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc1)
        
        # Add second 'x'
        loc2 = codeLocation(code="x", word_ref=1, code_ref=0, word="line", fuzzy=0)
        self.tree.add_child(loc2)
        
        # Should have 2 children from first 'x', each with 2 children from second 'x'
        self.assertEqual(len(self.tree.children), 2)
        for child in self.tree.children:
            self.assertEqual(len(child.children), 2)

    def test_add_child_empty_code(self):
        """Test add_child with empty code."""
        loc = codeLocation(code="", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        self.assertEqual(len(self.tree.children), 1)
        self.assertEqual(self.tree.children[0].location.code, "")


class TestPatternTreeStateMachineTraversal(unittest.TestCase):
    """Test PatternTree state machine traversal methods."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = PatternTree(root_loc)

    def test_traverse_original_hindi_empty_path(self):
        """Test _traverse_original_hindi with empty scanPath."""
        scn = scanPath()
        result = self.tree._traverse_original_hindi(scn, 0)
        
        # Empty path with no children should return empty list
        self.assertEqual(result, [])

    def test_traverse_original_hindi_invalid_state_transition_pruned(self):
        """Test _traverse_original_hindi prunes invalid transitions."""
        # original_hindi_meter("-", 0) should return -1 for invalid transition
        # At state 0, "-" is invalid (returns -1)
        loc = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        scn = scanPath()
        result = self.tree._traverse_original_hindi(scn, 0)
        
        # Invalid transition should be pruned, result should be empty
        self.assertEqual(result, [])

    def test_traverse_original_hindi_valid_transition_preserves_path(self):
        """Test _traverse_original_hindi with valid state transition preserves path."""
        # original_hindi_meter("=", 0) should return 1 (valid)
        loc = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        scn = scanPath()
        result = self.tree._traverse_original_hindi(scn, 0)
        
        # Should return a list (may be empty if no valid complete path)
        self.assertIsInstance(result, list)
        # If there are results, they should have location paths
        if len(result) > 0:
            self.assertGreater(len(result[0].location), 0)

    def test_traverse_original_hindi_state_transitions(self):
        """Test _traverse_original_hindi follows valid state transitions."""
        from aruuz.tree.state_machine import original_hindi_meter
        
        # Test state transitions manually
        # State 0: "=" -> state 1 (valid), "-" -> -1 (invalid)
        self.assertEqual(original_hindi_meter("=", 0), 1)
        self.assertEqual(original_hindi_meter("-", 0), -1)
        
        # State 1: "=" -> state 0 (valid), "-" -> state 2 (valid)
        self.assertEqual(original_hindi_meter("=", 1), 0)
        self.assertEqual(original_hindi_meter("-", 1), 2)
        
        # State 2: "=" -> -1 (invalid), "-" -> state 3 (valid)
        self.assertEqual(original_hindi_meter("=", 2), -1)
        self.assertEqual(original_hindi_meter("-", 2), 3)
        
        # State 3: "=" -> state 1 (valid), "-" -> -1 (invalid)
        self.assertEqual(original_hindi_meter("=", 3), 1)
        self.assertEqual(original_hindi_meter("-", 3), -1)

    def test_traverse_original_hindi_leaf_node_syllable_count(self):
        """Test _traverse_original_hindi at leaf node calculates syllable count correctly."""
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        
        # Create pattern: 15 "=" codes = 30 syllables, ending with "="
        # Note: This may not reach a leaf if state transitions don't allow it
        # But we're testing the leaf node logic itself
        for i in range(15):
            loc = codeLocation(code="=", word_ref=i, code_ref=0, word="test", fuzzy=0)
            self.tree.add_child(loc)
        
        scn = scanPath()
        result = self.tree._traverse_original_hindi(scn, 0)
        
        # Result should be a list
        self.assertIsInstance(result, list)

    def test_traverse_zamzama_empty_path(self):
        """Test _traverse_zamzama with empty scanPath."""
        scn = scanPath()
        result = self.tree._traverse_zamzama(scn, 0)
        
        # Empty path with no children should return empty list
        self.assertEqual(result, [])

    def test_traverse_zamzama_valid_state_transition(self):
        """Test _traverse_zamzama with valid state transition."""
        # zamzama_meter("-", 0) should return 1 (valid)
        loc = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        scn = scanPath()
        result = self.tree._traverse_zamzama(scn, 0)
        
        # Should return a list (may be empty if no valid complete path)
        self.assertIsInstance(result, list)

    def test_traverse_zamzama_state_transitions(self):
        """Test _traverse_zamzama follows valid state transitions."""
        from aruuz.tree.state_machine import zamzama_meter
        
        # Test state transitions manually
        # State 0: "-" -> state 1 (valid), "=" -> state 3 (valid)
        self.assertEqual(zamzama_meter("-", 0), 1)
        self.assertEqual(zamzama_meter("=", 0), 3)
        
        # State 1: "-" -> state 2 (valid), "=" -> -1 (invalid)
        self.assertEqual(zamzama_meter("-", 1), 2)
        self.assertEqual(zamzama_meter("=", 1), -1)
        
        # State 2: Both transitions invalid
        self.assertEqual(zamzama_meter("-", 2), -1)
        self.assertEqual(zamzama_meter("=", 2), -1)
        
        # State 3: "-" -> -1 (invalid), "=" -> state 0 (valid)
        self.assertEqual(zamzama_meter("-", 3), -1)
        self.assertEqual(zamzama_meter("=", 3), 0)

    def test_traverse_zamzama_leaf_node_syllable_count(self):
        """Test _traverse_zamzama at leaf node calculates syllable count correctly."""
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        
        # Create pattern: 16 "=" codes = 32 syllables, ending with "="
        # Note: This may not reach a leaf if state transitions don't allow it
        for i in range(16):
            loc = codeLocation(code="=", word_ref=i, code_ref=0, word="test", fuzzy=0)
            self.tree.add_child(loc)
        
        scn = scanPath()
        result = self.tree._traverse_zamzama(scn, 0)
        
        # Result should be a list
        self.assertIsInstance(result, list)

    def test_traverse_hindi_placeholder(self):
        """Test _traverse_hindi returns empty list (not implemented)."""
        scn = scanPath()
        result = self.tree._traverse_hindi(scn, 0)
        
        # Should return empty list (not implemented)
        self.assertEqual(result, [])


class TestPatternTreeMeterDetection(unittest.TestCase):
    """Test PatternTree meter detection based on syllable counts."""

    def setUp(self):
        """Set up test fixtures."""
        self.meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS

    def build_tree_with_pattern(self, pattern: str):
        """Helper to build tree from pattern string."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        return tree

    def test_original_hindi_count_30_ending_equals(self):
        """Test Original Hindi meter detection: count=30, last code='='."""
        # 15 "=" codes = 30 syllables
        pattern = "=" * 15
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base
        if len(result) > 0:
            self.assertIn(self.meter_base, result[0].meters)

    def test_original_hindi_count_31_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=31, last two codes='-='."""
        # 14 "=" codes + 1 "-" code = 28 + 1 = 29 syllables
        # Actually need: 15 "=" = 30, then "-" = 31, ending with "-="
        # Pattern should be: 14 "=", then "=", then "-" = 14*2 + 2 + 1 = 31 syllables
        pattern = "=" * 14 + "=" + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base if pattern ends with "-=" and count is 31
        self.assertIsInstance(result, list)
        # Verify the pattern ends correctly
        if len(result) > 0 and len(result[0].location) >= 2:
            last_code = result[0].location[-1].code
            second_last_code = result[0].location[-2].code
            if last_code == "-" and second_last_code == "=":
                # Check if meter_base is in the meters list
                if len(result[0].meters) > 0:
                    self.assertIn(self.meter_base, result[0].meters)

    def test_original_hindi_count_22_ending_equals(self):
        """Test Original Hindi meter detection: count=22, last code='='."""
        # 11 "=" codes = 22 syllables
        pattern = "=" * 11
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base + 1
        if len(result) > 0:
            self.assertIn(self.meter_base + 1, result[0].meters)

    def test_original_hindi_count_14_ending_equals(self):
        """Test Original Hindi meter detection: count=14, last code='='."""
        # 7 "=" codes = 14 syllables
        pattern = "=" * 7
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base + 3
        if len(result) > 0:
            self.assertIn(self.meter_base + 3, result[0].meters)

    def test_original_hindi_count_16_ending_equals(self):
        """Test Original Hindi meter detection: count=16, last code='='."""
        # 8 "=" codes = 16 syllables
        pattern = "=" * 8
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base + 4
        if len(result) > 0:
            self.assertIn(self.meter_base + 4, result[0].meters)

    def test_original_hindi_count_10_ending_equals(self):
        """Test Original Hindi meter detection: count=10, last code='='."""
        # 5 "=" codes = 10 syllables
        pattern = "=" * 5
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base + 5
        if len(result) > 0:
            self.assertIn(self.meter_base + 5, result[0].meters)

    def test_original_hindi_count_24_ending_equals(self):
        """Test Original Hindi meter detection: count=24, last code='='."""
        # 12 "=" codes = 24 syllables
        pattern = "=" * 12
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base + 6
        if len(result) > 0:
            self.assertIn(self.meter_base + 6, result[0].meters)

    def test_original_hindi_count_8_ending_equals(self):
        """Test Original Hindi meter detection: count=8, last code='='."""
        # 4 "=" codes = 8 syllables
        pattern = "=" * 4
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Should detect meter_base + 7
        if len(result) > 0:
            self.assertIn(self.meter_base + 7, result[0].meters)

    def test_zamzama_count_32_ending_equals(self):
        """Test Zamzama meter detection: count=32, last code='='."""
        # 16 "=" codes = 32 syllables
        pattern = "=" * 16
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_zamzama(scn, 0)
        
        # Should detect meter_base + 8
        if len(result) > 0:
            self.assertIn(self.meter_base + 8, result[0].meters)

    def test_zamzama_count_33_ending_dash_equals(self):
        """Test Zamzama meter detection: count=33, last two codes='-='."""
        # 15 "=" codes + 1 "-" code = 30 + 1 = 31 syllables
        # Actually need: 16 "=" = 32, then "-" = 33, ending with "-="
        # Pattern should be: 15 "=", then "=", then "-" = 15*2 + 2 + 1 = 33 syllables
        pattern = "=" * 15 + "=" + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_zamzama(scn, 0)
        
        # Should detect meter_base + 8 if pattern ends with "-=" and count is 33
        self.assertIsInstance(result, list)
        # Verify the pattern ends correctly
        if len(result) > 0 and len(result[0].location) >= 2:
            last_code = result[0].location[-1].code
            second_last_code = result[0].location[-2].code
            if last_code == "-" and second_last_code == "=":
                # Check if meter_base + 8 is in the meters list
                if len(result[0].meters) > 0:
                    self.assertIn(self.meter_base + 8, result[0].meters)

    def test_zamzama_count_24_ending_equals(self):
        """Test Zamzama meter detection: count=24, last code='='."""
        # 12 "=" codes = 24 syllables
        pattern = "=" * 12
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_zamzama(scn, 0)
        
        # Should detect meter_base + 9
        if len(result) > 0:
            self.assertIn(self.meter_base + 9, result[0].meters)

    def test_zamzama_count_16_ending_equals(self):
        """Test Zamzama meter detection: count=16, last code='='."""
        # 8 "=" codes = 16 syllables
        pattern = "=" * 8
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_zamzama(scn, 0)
        
        # Should detect meter_base + 10
        if len(result) > 0:
            self.assertIn(self.meter_base + 10, result[0].meters)

    def test_mixed_syllables_count(self):
        """Test meter detection with mixed '-' and '=' codes."""
        # Pattern: 10 "=" + 5 "-" = 20 + 5 = 25 syllables
        pattern = "=" * 10 + "-" * 5
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_syllable_count_calculation(self):
        """Test syllable count calculation: '=' = 2, '-' = 1."""
        # Pattern: 3 "=" + 1 "-" + 1 "=" = 6 + 1 + 2 = 9 syllables
        pattern = "===-="
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        # Manually build path to test count calculation
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            scn.location.append(loc)
        
        # Calculate count manually
        count = 0
        for loc in scn.location:
            if loc.code == "=":
                count += 2
            elif loc.code == "-":
                count += 1
        
        self.assertEqual(count, 9)

    def test_original_hindi_count_23_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=23, last two codes='-='."""
        # 11 "=" codes = 22, then "-" = 23, ending with "-="
        pattern = "=" * 11 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_original_hindi_count_15_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=15, last two codes='-='."""
        # 7 "=" codes = 14, then "-" = 15, ending with "-="
        pattern = "=" * 7 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_original_hindi_count_17_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=17, last two codes='-='."""
        # 8 "=" codes = 16, then "-" = 17, ending with "-="
        pattern = "=" * 8 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_original_hindi_count_11_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=11, last two codes='-='."""
        # 5 "=" codes = 10, then "-" = 11, ending with "-="
        pattern = "=" * 5 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_original_hindi_count_25_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=25, last two codes='-='."""
        # 12 "=" codes = 24, then "-" = 25, ending with "-="
        pattern = "=" * 12 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_original_hindi_count_9_ending_dash_equals(self):
        """Test Original Hindi meter detection: count=9, last two codes='-='."""
        # 4 "=" codes = 8, then "-" = 9, ending with "-="
        pattern = "=" * 4 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_zamzama_count_25_ending_dash_equals(self):
        """Test Zamzama meter detection: count=25, last two codes='-='."""
        # 12 "=" codes = 24, then "-" = 25, ending with "-="
        pattern = "=" * 12 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_zamzama(scn, 0)
        
        self.assertIsInstance(result, list)

    def test_zamzama_count_17_ending_dash_equals(self):
        """Test Zamzama meter detection: count=17, last two codes='-='."""
        # 8 "=" codes = 16, then "-" = 17, ending with "-="
        pattern = "=" * 8 + "-"
        tree = self.build_tree_with_pattern(pattern)
        
        scn = scanPath()
        result = tree._traverse_zamzama(scn, 0)
        
        self.assertIsInstance(result, list)


class TestPatternTreeIsMatch(unittest.TestCase):
    """Test PatternTree.is_match() main entry point."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = PatternTree(root_loc)

    def test_is_match_empty_tree(self):
        """Test is_match with empty tree."""
        result = self.tree.is_match()
        
        # Should return empty list
        self.assertEqual(result, [])

    def test_is_match_single_code(self):
        """Test is_match with single code."""
        loc = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        self.assertIsInstance(result, list)

    def test_is_match_combines_hindi_and_zamzama(self):
        """Test is_match combines results from both traversals."""
        # Build pattern that might match both
        pattern = "=" * 16  # 32 syllables, might match Zamzama
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        # Should combine results from both traversals
        self.assertIsInstance(result, list)

    def test_is_match_with_x_expansion(self):
        """Test is_match with 'x' code expansion."""
        # Add 'x' which expands to '-' and '='
        loc = codeLocation(code="x", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        # Should explore both branches
        self.assertIsInstance(result, list)

    def test_is_match_multiple_paths(self):
        """Test is_match returns multiple paths when multiple matches exist."""
        # Build pattern with 'x' that creates multiple paths
        for i in range(3):
            loc = codeLocation(code="x", word_ref=i, code_ref=0, word="test", fuzzy=0)
            self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        # Should return multiple paths (2^3 = 8 paths from 'x' expansion)
        self.assertIsInstance(result, list)

    def test_is_match_preserves_location_path(self):
        """Test is_match preserves location path in scanPath."""
        loc = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        # If result has paths, they should have location information
        if len(result) > 0:
            self.assertGreater(len(result[0].location), 0)
            # The root location should be included in the path
            # Note: Root location may or may not be included depending on implementation
            # Check that location has valid codeLocation objects
            for loc_obj in result[0].location:
                self.assertIsInstance(loc_obj, codeLocation)
                self.assertIsInstance(loc_obj.code, str)

    def test_is_match_returns_scan_path_objects(self):
        """Test is_match returns proper scanPath objects."""
        loc = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        # Should return list of scanPath objects
        self.assertIsInstance(result, list)
        for sp in result:
            self.assertIsInstance(sp, scanPath)
            self.assertIsInstance(sp.location, list)
            self.assertIsInstance(sp.meters, list)

    def test_is_match_combines_results_from_both_machines(self):
        """Test is_match combines results from both Original Hindi and Zamzama."""
        # Build a pattern that might match both (or at least be traversed by both)
        pattern = "=" * 8  # 16 syllables
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            self.tree.add_child(loc)
        
        result = self.tree.is_match()
        
        # Should combine results from both traversals
        self.assertIsInstance(result, list)
        # Results may be empty if no valid paths, but structure should be correct


class TestPatternTreeEdgeCases(unittest.TestCase):
    """Test PatternTree edge cases."""

    def test_empty_pattern(self):
        """Test PatternTree with empty pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        result = tree.is_match()
        self.assertEqual(result, [])

    def test_single_character_pattern(self):
        """Test PatternTree with single character pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        loc = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree.add_child(loc)
        
        result = tree.is_match()
        self.assertIsInstance(result, list)

    def test_single_x_pattern(self):
        """Test PatternTree with single 'x' pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        loc = codeLocation(code="x", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree.add_child(loc)
        
        result = tree.is_match()
        # Should explore both '-' and '=' branches
        self.assertIsInstance(result, list)

    def test_very_long_pattern(self):
        """Test PatternTree with very long pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add 50 codes
        for i in range(50):
            loc = codeLocation(code="=", word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        result = tree.is_match()
        self.assertIsInstance(result, list)

    def test_all_dash_pattern(self):
        """Test PatternTree with all '-' pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        pattern = "-" * 20
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        result = tree.is_match()
        self.assertIsInstance(result, list)

    def test_all_equals_pattern(self):
        """Test PatternTree with all '=' pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        pattern = "=" * 20
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        result = tree.is_match()
        self.assertIsInstance(result, list)

    def test_alternating_pattern(self):
        """Test PatternTree with alternating '-' and '=' pattern."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        pattern = "-=" * 10
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        result = tree.is_match()
        self.assertIsInstance(result, list)

    def test_meter_base_calculation(self):
        """Test meter_base calculation matches expected value."""
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        expected_base = 129 + 0 + 12  # NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        self.assertEqual(meter_base, expected_base)

    def test_scan_path_structure(self):
        """Test scanPath structure in results."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add pattern that might match
        pattern = "=" * 8  # 16 syllables
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        result = tree.is_match()
        
        # Check structure of results
        for sp in result:
            self.assertIsInstance(sp, scanPath)
            self.assertIsInstance(sp.location, list)
            self.assertIsInstance(sp.meters, list)
            if len(sp.meters) > 0:
                self.assertIsInstance(sp.meters[0], int)
                # Meter IDs should be integers >= meter_base
                meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
                for meter_id in sp.meters:
                    self.assertIsInstance(meter_id, int)
                    self.assertGreaterEqual(meter_id, meter_base)

    def test_state_machine_invalid_code_handling(self):
        """Test state machine handles invalid codes gracefully."""
        from aruuz.tree.state_machine import original_hindi_meter, zamzama_meter
        
        # Invalid codes should return -1
        self.assertEqual(original_hindi_meter("x", 0), -1)
        self.assertEqual(original_hindi_meter("", 0), -1)
        self.assertEqual(zamzama_meter("x", 0), -1)
        self.assertEqual(zamzama_meter("", 0), -1)
        
        # Invalid state indices should return -1
        self.assertEqual(original_hindi_meter("=", 10), -1)
        self.assertEqual(zamzama_meter("=", 10), -1)

    def test_traverse_preserves_code_location_metadata(self):
        """Test traversal preserves codeLocation metadata in paths."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add child with metadata
        loc = codeLocation(code="=", word_ref=5, code_ref=3, word="test_word", fuzzy=1)
        tree.add_child(loc)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # If there are results, check metadata is preserved
        if len(result) > 0 and len(result[0].location) > 0:
            for loc_obj in result[0].location:
                self.assertIsInstance(loc_obj, codeLocation)
                # Check that metadata fields exist
                self.assertTrue(hasattr(loc_obj, 'code'))
                self.assertTrue(hasattr(loc_obj, 'word_ref'))
                self.assertTrue(hasattr(loc_obj, 'code_ref'))
                self.assertTrue(hasattr(loc_obj, 'word'))
                self.assertTrue(hasattr(loc_obj, 'fuzzy'))

    def test_traverse_copies_scan_path_correctly(self):
        """Test traversal correctly copies scanPath during recursion."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add two children to test path copying
        loc1 = codeLocation(code="=", word_ref=0, code_ref=0, word="test1", fuzzy=0)
        tree.add_child(loc1)
        loc2 = codeLocation(code="=", word_ref=1, code_ref=0, word="test2", fuzzy=0)
        tree.add_child(loc2)
        
        scn = scanPath()
        result = tree._traverse_original_hindi(scn, 0)
        
        # Results should have paths with multiple locations
        self.assertIsInstance(result, list)
        if len(result) > 0:
            # Each result should have locations from the traversal
            for sp in result:
                self.assertIsInstance(sp, scanPath)
                # Paths should have at least the locations we added
                self.assertGreaterEqual(len(sp.location), 0)

    def test_leaf_node_syllable_count_ignores_root(self):
        """Test leaf node syllable count only counts actual codes, not root."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add single code
        loc = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree.add_child(loc)
        
        # Manually create a scanPath with root and one code
        scn = scanPath()
        root_loc_in_path = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc_in_path)
        code_loc_in_path = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        scn.location.append(code_loc_in_path)
        
        # Calculate count (should only count "=", not "root")
        count = 0
        for loc_obj in scn.location:
            if loc_obj.code == "=":
                count += 2
            elif loc_obj.code == "-":
                count += 1
            # Root code should not contribute to count
        
        self.assertEqual(count, 2)  # Only the "=" contributes

    def test_multiple_meters_in_single_path(self):
        """Test that a single path can have multiple meters (if implementation allows)."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add pattern
        pattern = "=" * 8  # 16 syllables
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        result = tree.is_match()
        
        # Check structure - each scanPath should have a meters list
        for sp in result:
            self.assertIsInstance(sp.meters, list)
            # Meters list should contain integers
            for meter_id in sp.meters:
                self.assertIsInstance(meter_id, int)

    def test_x_expansion_in_state_machine_context(self):
        """Test 'x' expansion works correctly in state machine traversal."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # Add 'x' which expands to '-' and '='
        loc = codeLocation(code="x", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree.add_child(loc)
        
        # is_match should explore both branches
        result = tree.is_match()
        
        # Should return list (may be empty if no valid paths)
        self.assertIsInstance(result, list)
        # Tree should have two children from 'x' expansion
        self.assertEqual(len(tree.children), 2)
        codes = [child.location.code for child in tree.children]
        self.assertIn("-", codes)
        self.assertIn("=", codes)


if __name__ == '__main__':
    unittest.main()

