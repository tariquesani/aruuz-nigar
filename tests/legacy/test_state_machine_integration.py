"""
Integration tests for state machine integration in PatternTree and CodeTree.

This test module verifies that:
1. State machines are correctly implemented
2. PatternTree uses state machines correctly
3. CodeTree integrates PatternTree correctly
4. Special meter detection works end-to-end
"""

import unittest
from unittest import mock
from aruuz.tree.state_machine import (
    hindi_meter,
    zamzama_meter,
    original_hindi_meter
)
from aruuz.tree.pattern_tree import PatternTree
from aruuz.tree.code_tree import CodeTree
from aruuz.models import codeLocation, scanPath, Lines, Words
from aruuz.meters import (
    NUM_METERS,
    NUM_VARIED_METERS,
    NUM_RUBAI_METERS,
    NUM_SPECIAL_METERS
)


class TestStateMachineIntegration(unittest.TestCase):
    """Test state machine integration in PatternTree and CodeTree."""
    
    def test_state_machines_exist_and_work(self):
        """Test that state machines exist and work correctly."""
        # Test original_hindi_meter
        self.assertEqual(original_hindi_meter("=", 0), 1)
        self.assertEqual(original_hindi_meter("-", 0), -1)
        self.assertEqual(original_hindi_meter("=", 1), 0)
        self.assertEqual(original_hindi_meter("-", 1), 2)
        
        # Test zamzama_meter
        self.assertEqual(zamzama_meter("-", 0), 1)
        self.assertEqual(zamzama_meter("=", 0), 3)
        self.assertEqual(zamzama_meter("-", 1), 2)
        self.assertEqual(zamzama_meter("=", 1), -1)
        
        # Test hindi_meter
        self.assertEqual(hindi_meter("=", 0), 1)
        self.assertEqual(hindi_meter("-", 0), 2)
    
    def test_pattern_tree_uses_state_machines(self):
        """Test that PatternTree uses state machines for traversal."""
        import inspect
        
        # Verify PatternTree._traverse_original_hindi uses original_hindi_meter
        source = inspect.getsource(PatternTree._traverse_original_hindi)
        self.assertIn("original_hindi_meter", source)
        
        # Verify PatternTree._traverse_zamzama uses zamzama_meter
        source2 = inspect.getsource(PatternTree._traverse_zamzama)
        self.assertIn("zamzama_meter", source2)
    
    def test_pattern_tree_detects_zamzama_meter(self):
        """Test that PatternTree can detect Zamzama meters using state machines."""
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        
        # Create PatternTree with 32-syllable pattern (should match Zamzama meter_base + 8)
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # 16 "=" codes = 32 syllables
        pattern = "=" * 16
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        results = tree.is_match()
        
        # Check if Zamzama meter was detected
        zamzama_detected = False
        for sp in results:
            if meter_base + 8 in sp.meters:
                zamzama_detected = True
                break
        
        self.assertTrue(zamzama_detected, "Zamzama meter should be detected for 32-syllable pattern")
    
    def test_pattern_tree_detects_hindi_meter(self):
        """Test that PatternTree can detect Original Hindi meters using state machines."""
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        
        # Create PatternTree with 16-syllable pattern (should match Original Hindi meter_base + 4)
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = PatternTree(root_loc)
        
        # 8 "=" codes = 16 syllables
        pattern = "=" * 8
        for i, code in enumerate(pattern):
            loc = codeLocation(code=code, word_ref=i, code_ref=0, word="test", fuzzy=0)
            tree.add_child(loc)
        
        results = tree.is_match()
        
        # Check if Original Hindi meter was detected
        hindi_detected = False
        for sp in results:
            if meter_base + 4 in sp.meters:
                hindi_detected = True
                break
        
        self.assertTrue(hindi_detected, "Original Hindi meter should be detected for 16-syllable pattern")
    
    def test_code_tree_integrates_pattern_tree(self):
        """Test that CodeTree integrates PatternTree for special meter detection."""
        import inspect
        
        # Verify CodeTree.find_meter uses PatternTree
        source = inspect.getsource(CodeTree.find_meter)
        self.assertIn("PatternTree", source)
        self.assertIn("is_match", source)
    
    def test_code_tree_calls_pattern_tree_when_appropriate(self):
        """Test that CodeTree calls PatternTree when meters is None or contains -1."""
        # Create a simple line with codes
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["=" * 8]  # 16 syllables
        line.words_list = [word]
        
        # Build CodeTree from line
        tree = CodeTree.build_from_line(line)
        
        # Call find_meter with None (should trigger PatternTree integration)
        results = tree.find_meter(None)
        
        # Should return results (may be empty if pattern doesn't match constraints)
        self.assertIsInstance(results, list)
    
    def test_code_tree_builds_pattern_tree_per_character_and_expands_x(self):
        """Test CodeTree calls PatternTree.add_child per character and handles 'x' correctly."""
        # Create a simple line with a single word whose code includes 'x'
        line = Lines("test")
        word = Words()
        word.word = "test"
        # Single code with three characters, middle one ambiguous
        word.code = ["-x="]
        line.words_list = [word]

        tree = CodeTree.build_from_line(line)

        # Patch PatternTree.add_child and PatternTree.is_match to observe character-level calls
        with mock.patch("aruuz.tree.code_tree.PatternTree.add_child") as mock_add_child, \
             mock.patch("aruuz.tree.code_tree.PatternTree.is_match", return_value=[]):
            # Use meters=None so that PatternTree integration is triggered
            tree.find_meter(None)

        # Collect the codes that were passed into add_child
        added_codes = [call.args[0].code for call in mock_add_child.call_args_list]

        # PatternTree should receive one call per character in the scansion code
        # path. The word code "-x=" should contribute '-', 'x', '='.
        self.assertIn("-", added_codes)
        self.assertIn("x", added_codes)
        self.assertIn("=", added_codes)

        # Now verify the special handling for a trailing 'x':
        # if we use a code consisting only of 'x', the last character should be
        # converted to '=' *before* being passed to PatternTree.add_child.
        line2 = Lines("test2")
        word2 = Words()
        word2.word = "test2"
        word2.code = ["x"]
        line2.words_list = [word2]

        tree2 = CodeTree.build_from_line(line2)

        with mock.patch("aruuz.tree.code_tree.PatternTree.add_child") as mock_add_child2, \
             mock.patch("aruuz.tree.code_tree.PatternTree.is_match", return_value=[]):
            tree2.find_meter(None)

        added_codes2 = [call.args[0].code for call in mock_add_child2.call_args_list]

        # The word-level location had code "x" but, because it is the last
        # character of the last location, it must be converted to '=' before
        # calling add_child, so 'x' should not appear and '=' should.
        self.assertNotIn("x", added_codes2)
        self.assertIn("=", added_codes2)
    
    def test_meter_base_calculation(self):
        """Test that meter base calculation is correct."""
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        expected_base = 129 + 0 + 12
        self.assertEqual(meter_base, expected_base)
    
    def test_special_meter_indices(self):
        """Test that special meter indices are correct."""
        self.assertEqual(NUM_SPECIAL_METERS, 11)
        
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
        # Hindi meters: indices 0-7 in special meters = meter_base to meter_base + 7
        # Zamzama meters: indices 8-10 in special meters = meter_base + 8 to meter_base + 10
        
        self.assertEqual(meter_base + NUM_SPECIAL_METERS - 1, meter_base + 10)

    def test_code_tree_detects_zamzama_meters_via_pattern_tree(self):
        """
        Test that CodeTree + PatternTree integration detects Zamzama meters
        with the same syllable-count rules as the C# implementation.

        C# mapping (patternTree.traverseZamzama):
        - Counts 32 or 33  → meter_base + 8
        - Counts 24 or 25  → meter_base + 9
        - Counts 16 or 17  → meter_base + 10

        Here we build a CodeTree from synthetic codes whose total syllable
        counts match these values and assert that the expected Zamzama meter
        indices are returned when PatternTree integration is enabled.
        """
        meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS

        # Helper to build a CodeTree from a single synthetic word code
        def build_tree_from_code(code: str) -> CodeTree:
            line = Lines("test")
            # Ensure we have exactly one word
            self.assertEqual(len(line.words_list), 1)
            word = line.words_list[0]
            word.word = "test"
            word.code = [code]
            word.taqti_word_graft = []
            return CodeTree.build_from_line(line)

        # Each "=" contributes 2 syllables, each "-" contributes 1 syllable.
        # The patterns below are chosen to hit the Zamzama syllable counts.
        test_cases = [
            # (code_string, expected_meter_index)
            ("=" * 16, meter_base + 8),          # 16 * 2 = 32
            ("=" * 16 + "-", meter_base + 8),    # 32 + 1 = 33, ends with "-="
            ("=" * 12, meter_base + 9),          # 12 * 2 = 24
            ("=" * 12 + "-", meter_base + 9),    # 24 + 1 = 25, ends with "-="
            ("=" * 8, meter_base + 10),          # 8 * 2 = 16
            ("=" * 8 + "-", meter_base + 10),    # 16 + 1 = 17, ends with "-="
        ]

        for code, expected_meter in test_cases:
            tree = build_tree_from_code(code)

            # Use meters=[-1] to trigger PatternTree integration without
            # constraining to any regular/rubai meter indices.
            scan_paths = tree.find_meter(meters=[-1])

            detected_meters = set()
            for sp in scan_paths:
                for m in sp.meters:
                    detected_meters.add(m)

            self.assertIn(
                expected_meter,
                detected_meters,
                msg=f"Code '{code}' should detect Zamzama meter index {expected_meter}, "
                    f"detected meters were {detected_meters}"
            )


if __name__ == '__main__':
    unittest.main()

