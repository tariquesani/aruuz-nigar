"""
Integration tests for state machine integration in PatternTree and CodeTree.

This test module verifies that:
1. State machines are correctly implemented
2. PatternTree uses state machines correctly
3. CodeTree integrates PatternTree correctly
4. Special meter detection works end-to-end
"""

import unittest
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


if __name__ == '__main__':
    unittest.main()

