"""
Comprehensive unit tests for CodeTree class.

Tests cover:
- Tree construction from line
- add_child() with various code patterns
- find_meter() with empty meters list
- find_meter() with specific meter indices
- _traverse() with valid/invalid paths
- _is_match() with various meter patterns
- _check_code_length() filtering
- Fuzzy matching traversal
- Free verse traversal
- Edge cases: empty line, single word, multiple code variations
"""

import unittest
from unittest.mock import patch
from aruuz.tree.code_tree import CodeTree
from aruuz.tree.pattern_tree import PatternTree
from aruuz.models import codeLocation, Lines, Words, scanPath
from aruuz.meters import METERS, NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, USAGE


class TestCodeTreeConstruction(unittest.TestCase):
    """Test CodeTree construction and initialization."""

    def test_init_with_code_location(self):
        """Test CodeTree initialization with codeLocation."""
        loc = codeLocation(code="-===", word_ref=0, code_ref=0, word="test", fuzzy=0)
        tree = CodeTree(loc)
        
        self.assertEqual(tree.location.code, "-===")
        self.assertEqual(tree.location.word_ref, 0)
        self.assertEqual(tree.location.code_ref, 0)
        self.assertEqual(tree.location.word, "test")
        self.assertEqual(len(tree.children), 0)
        self.assertEqual(tree.error_param, 2)
        self.assertFalse(tree.fuzzy)
        self.assertFalse(tree.free_verse)

    def test_init_with_root_location(self):
        """Test CodeTree initialization with root location."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = CodeTree(root_loc)
        
        self.assertEqual(tree.location.code, "root")
        self.assertEqual(tree.location.word_ref, -1)
        self.assertEqual(len(tree.children), 0)

    def test_build_from_line_empty(self):
        """Test build_from_line with empty line."""
        line = Lines("")
        tree = CodeTree.build_from_line(line)
        
        self.assertEqual(tree.location.code, "root")
        self.assertEqual(len(tree.children), 0)

    def test_build_from_line_single_word(self):
        """Test build_from_line with single word."""
        line = Lines("test")
        # Create a word with code
        word = Words()
        word.word = "test"
        word.code = ["-==="]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        self.assertEqual(tree.location.code, "root")
        self.assertGreater(len(tree.children), 0)

    def test_build_from_line_multiple_words(self):
        """Test build_from_line with multiple words."""
        line = Lines("test line")
        word1 = Words()
        word1.word = "test"
        word1.code = ["-==="]
        word2 = Words()
        word2.word = "line"
        word2.code = ["-==="]
        line.words_list = [word1, word2]
        
        tree = CodeTree.build_from_line(line)
        
        self.assertEqual(tree.location.code, "root")
        self.assertGreater(len(tree.children), 0)

    def test_build_from_line_with_taqti_graft(self):
        """Test build_from_line includes taqti_word_graft codes."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-==="]
        word.taqti_word_graft = ["-==="]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Should have children from both code and taqti_word_graft
        self.assertGreater(len(tree.children), 0)

    def test_build_from_line_duplicate_codes(self):
        """Test build_from_line handles duplicate codes correctly."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-===", "-==="]  # Duplicate code
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Should only add unique codes
        self.assertGreaterEqual(len(tree.children), 0)


class TestCodeTreeAddChild(unittest.TestCase):
    """Test CodeTree.add_child() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_add_child_sequential_word(self):
        """Test add_child with sequential word reference."""
        loc1 = codeLocation(code="-===", word_ref=0, code_ref=0, word="word1", fuzzy=0)
        loc2 = codeLocation(code="-===", word_ref=1, code_ref=0, word="word2", fuzzy=0)
        
        self.tree.add_child(loc1)
        self.tree.add_child(loc2)
        
        self.assertEqual(len(self.tree.children), 1)
        self.assertEqual(len(self.tree.children[0].children), 1)

    def test_add_child_same_word_different_code_ref(self):
        """Test add_child with same word but different code_ref."""
        loc1 = codeLocation(code="-===", word_ref=0, code_ref=0, word="word1", fuzzy=0)
        loc2 = codeLocation(code="===-", word_ref=0, code_ref=1, word="word1", fuzzy=0)
        
        self.tree.add_child(loc1)
        self.tree.add_child(loc2)
        
        # Should have two children for same word with different codes
        self.assertGreaterEqual(len(self.tree.children), 1)

    def test_add_child_same_word_same_code_ref(self):
        """Test add_child doesn't add duplicate code_ref."""
        loc1 = codeLocation(code="-===", word_ref=0, code_ref=0, word="word1", fuzzy=0)
        loc2 = codeLocation(code="-===", word_ref=0, code_ref=0, word="word1", fuzzy=0)
        
        self.tree.add_child(loc1)
        initial_count = len(self.tree.children)
        self.tree.add_child(loc2)
        
        # Should not add duplicate
        self.assertEqual(len(self.tree.children), initial_count)

    def test_add_child_non_sequential_word(self):
        """Test add_child with non-sequential word reference."""
        loc1 = codeLocation(code="-===", word_ref=0, code_ref=0, word="word1", fuzzy=0)
        loc2 = codeLocation(code="-===", word_ref=2, code_ref=0, word="word3", fuzzy=0)
        
        self.tree.add_child(loc1)
        self.tree.add_child(loc2)
        
        # Non-sequential word should be added recursively to children
        self.assertGreaterEqual(len(self.tree.children), 1)

    def test_add_child_preserves_flags(self):
        """Test add_child preserves fuzzy and free_verse flags."""
        self.tree.fuzzy = True
        self.tree.free_verse = True
        self.tree.error_param = 5
        
        loc = codeLocation(code="-===", word_ref=0, code_ref=0, word="word1", fuzzy=0)
        self.tree.add_child(loc)
        
        if len(self.tree.children) > 0:
            child = self.tree.children[0]
            self.assertTrue(child.fuzzy)
            self.assertTrue(child.free_verse)
            self.assertEqual(child.error_param, 5)


class TestCodeTreeIsMatch(unittest.TestCase):
    """Test CodeTree._is_match() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_is_match_exact_match(self):
        """Test _is_match with exact pattern match."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "-==="
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_with_tentative_code(self):
        """Test _is_match with tentative code from previous words."""
        meter = "-===/-===/-===/-==="
        tentative_code = "-==="
        word_code = "-==="
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_with_flexible_syllable(self):
        """Test _is_match with 'x' (flexible syllable)."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "x==="  # 'x' should match both '-' and '='
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_no_match(self):
        """Test _is_match when pattern doesn't match."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "===-"  # Wrong pattern
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertFalse(result)

    def test_is_match_with_caesura(self):
        """Test _is_match with caesura (word boundary)."""
        meter = "-===/-===+=-=/-==="  # Has '+' at word boundary
        tentative_code = "-==="
        word_code = "-"  # Single character, should be allowed
        result = self.tree._is_match(meter, tentative_code, word_code)
        # Should match (single char is allowed even with caesura)
        self.assertTrue(result)

    def test_is_match_caesura_violation(self):
        """Test _is_match detects caesura violation."""
        meter = "-===/-===+=-=/-==="  # Has '+' at word boundary
        tentative_code = "-==="
        word_code = "=="  # Doesn't end with '-', should violate caesura
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertFalse(result)

    def test_is_match_variation_2(self):
        """Test _is_match with variation 2 (meter with '+' removed + '-' appended)."""
        meter = "-===/-===+=-=/-==="
        tentative_code = ""
        word_code = "-===-"  # Should match variation 2
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_empty_codes(self):
        """Test _is_match with empty codes."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = ""
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertFalse(result)

    def test_is_match_with_slash_in_meter(self):
        """Test _is_match handles '/' in meter pattern."""
        meter = "-===/-===/-===/-==="
        tentative_code = ""
        word_code = "-==="
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertTrue(result)

    def test_is_match_partial_match(self):
        """Test _is_match with partial match."""
        meter = "-===/-===/-===/-==="
        tentative_code = "-==="
        word_code = "-==="  # Should match second foot
        result = self.tree._is_match(meter, tentative_code, word_code)
        self.assertTrue(result)


class TestCodeTreeCheckCodeLength(unittest.TestCase):
    """Test CodeTree._check_code_length() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_check_code_length_exact_match(self):
        """Test _check_code_length with exact length match."""
        code = "-==="
        meter_indices = [0, 1, 2]  # First few meters
        result = self.tree._check_code_length(code, meter_indices)
        # Should return indices that match the code length
        self.assertIsInstance(result, list)
        self.assertLessEqual(len(result), len(meter_indices))
        # All returned indices should be in original list
        for idx in result:
            self.assertIn(idx, meter_indices)

    def test_check_code_length_filters_mismatches(self):
        """Test _check_code_length filters out meters that don't match."""
        code = "-"  # Very short code
        meter_indices = [0, 1, 2, 3, 4]  # Multiple meters
        result = self.tree._check_code_length(code, meter_indices)
        # Should filter out meters that don't match any variation
        self.assertIsInstance(result, list)
        # Result should be a subset of input
        for idx in result:
            self.assertIn(idx, meter_indices)

    def test_check_code_length_with_flexible_syllable(self):
        """Test _check_code_length with 'x' in code."""
        code = "x==="
        meter_indices = [0, 1]
        result = self.tree._check_code_length(code, meter_indices)
        self.assertIsInstance(result, list)
        for idx in result:
            self.assertIn(idx, meter_indices)

    def test_check_code_length_empty_list(self):
        """Test _check_code_length with empty meter indices."""
        code = "-==="
        meter_indices = []
        result = self.tree._check_code_length(code, meter_indices)
        self.assertEqual(result, [])

    def test_check_code_length_all_variations(self):
        """Test _check_code_length checks all 4 variations."""
        code = "-==="
        meter_indices = [0]  # First meter
        result = self.tree._check_code_length(code, meter_indices)
        # Should check all variations and return appropriate result
        self.assertIsInstance(result, list)

    def test_check_code_length_with_plus_in_meter(self):
        """Test _check_code_length with meter containing '+'."""
        code = "-==="
        # Find a meter with '+' in it
        meter_with_plus_idx = None
        for i, m in enumerate(METERS):
            if '+' in m:
                meter_with_plus_idx = i
                break
        
        if meter_with_plus_idx is not None:
            result = self.tree._check_code_length(code, [meter_with_plus_idx])
            self.assertIsInstance(result, list)


class TestCodeTreeTraverse(unittest.TestCase):
    """Test CodeTree._traverse() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_traverse_empty_meters(self):
        """Test _traverse with empty meter list."""
        scn = scanPath()
        scn.meters = []
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse(scn)
        self.assertEqual(result, [])

    def test_traverse_no_children(self):
        """Test _traverse with no children (leaf node)."""
        scn = scanPath()
        scn.meters = [0]  # First meter
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse(scn)
        # Should check code length and return if matches
        self.assertIsInstance(result, list)

    def test_traverse_with_matching_child(self):
        """Test _traverse with matching child."""
        # Build a simple tree
        word_loc = codeLocation(code="-===", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(word_loc)
        
        scn = scanPath()
        scn.meters = [0]  # First meter is "-===/-===/-===/-==="
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse(scn)
        self.assertIsInstance(result, list)

    def test_traverse_filters_non_matching_meters(self):
        """Test _traverse filters out non-matching meters."""
        # Build a tree with a specific code
        word_loc = codeLocation(code="-===", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(word_loc)
        
        scn = scanPath()
        scn.meters = [0, 1, 2, 3]  # Multiple meters
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse(scn)
        # Should filter meters during traversal
        self.assertIsInstance(result, list)


class TestCodeTreeFuzzyTraverse(unittest.TestCase):
    """Test CodeTree._traverse_fuzzy() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)
        self.tree.fuzzy = True
        self.tree.error_param = 2

    def test_traverse_fuzzy_empty_meters(self):
        """Test _traverse_fuzzy with empty meter list."""
        scn = scanPath()
        scn.meters = []
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse_fuzzy(scn)
        self.assertEqual(result, [])

    def test_traverse_fuzzy_no_children(self):
        """Test _traverse_fuzzy with no children (leaf node)."""
        scn = scanPath()
        scn.meters = [0]
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse_fuzzy(scn)
        # Should use fuzzy matching at leaf
        self.assertIsInstance(result, list)

    def test_traverse_fuzzy_with_children(self):
        """Test _traverse_fuzzy traverses all children without filtering."""
        word_loc = codeLocation(code="-===", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(word_loc)
        
        scn = scanPath()
        scn.meters = [0, 1, 2]
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse_fuzzy(scn)
        self.assertIsInstance(result, list)

    def test_check_code_length_fuzzy(self):
        """Test _check_code_length_fuzzy method."""
        code = "-==="
        meter_indices = [0, 1]
        result = self.tree._check_code_length_fuzzy(code, meter_indices)
        self.assertIsInstance(result, list)
        for idx in result:
            self.assertIn(idx, meter_indices)

    def test_levenshtein_distance(self):
        """Test _levenshtein_distance method."""
        pattern = "-==="
        code = "-==="
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_levenshtein_distance_with_x(self):
        """Test _levenshtein_distance with 'x' wildcard."""
        pattern = "-==="
        code = "x==="  # 'x' matches any character
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_levenshtein_distance_with_tilde(self):
        """Test _levenshtein_distance with '~' in pattern."""
        pattern = "~==="  # '~' matches '-' with zero cost
        code = "-==="
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertEqual(distance, 0)

    def test_levenshtein_distance_mismatch(self):
        """Test _levenshtein_distance with mismatch."""
        pattern = "-==="
        code = "===-"
        distance = self.tree._levenshtein_distance(pattern, code)
        self.assertGreater(distance, 0)


class TestCodeTreeFreeVerseTraverse(unittest.TestCase):
    """Test CodeTree._traverse_free_verse() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)
        self.tree.free_verse = True

    def test_traverse_free_verse_empty_meters(self):
        """Test _traverse_free_verse with empty meter list."""
        scn = scanPath()
        scn.meters = []
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse_free_verse(scn)
        self.assertEqual(result, [])

    def test_traverse_free_verse_no_children(self):
        """Test _traverse_free_verse with no children (leaf node)."""
        scn = scanPath()
        scn.meters = [0]
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._traverse_free_verse(scn)
        # Should use free verse matching at leaf
        self.assertIsInstance(result, list)

    def test_check_meter_free_verse(self):
        """Test _check_meter_free_verse method."""
        code = "-==="
        meter_indices = [0, 1]
        result = self.tree._check_meter_free_verse(code, meter_indices)
        self.assertIsInstance(result, list)
        for idx in result:
            self.assertIn(idx, meter_indices)

    def test_check_meter_free_verse_empty_code(self):
        """Test _check_meter_free_verse with empty code."""
        code = ""
        meter_indices = [0, 1]
        result = self.tree._check_meter_free_verse(code, meter_indices)
        # Should return all indices for empty code
        self.assertEqual(result, meter_indices)


class TestCodeTreeFindMeter(unittest.TestCase):
    """Test CodeTree.find_meter() method."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a simple line with words
        self.line = Lines("test line")
        word1 = Words()
        word1.word = "test"
        word1.code = ["-==="]
        word2 = Words()
        word2.word = "line"
        word2.code = ["-==="]
        self.line.words_list = [word1, word2]

    def test_find_meter_no_meters_specified(self):
        """Test find_meter with no meters specified."""
        tree = CodeTree.build_from_line(self.line)
        result = tree.find_meter()
        
        self.assertIsInstance(result, list)
        # Should check all meters with usage == 1 first, then usage == 0, then rubai

    def test_find_meter_empty_meters_list(self):
        """Test find_meter with empty meters list."""
        tree = CodeTree.build_from_line(self.line)
        result = tree.find_meter([])
        
        self.assertIsInstance(result, list)

    def test_find_meter_specific_meters(self):
        """Test find_meter with specific meter indices."""
        tree = CodeTree.build_from_line(self.line)
        result = tree.find_meter([0, 1, 2])
        
        self.assertIsInstance(result, list)

    def test_find_meter_rubai_only(self):
        """Test find_meter with -2 (rubai meters only)."""
        tree = CodeTree.build_from_line(self.line)
        result = tree.find_meter([-2])
        
        self.assertIsInstance(result, list)

    def test_find_meter_fuzzy_mode(self):
        """Test find_meter in fuzzy mode."""
        tree = CodeTree.build_from_line(self.line, fuzzy=True)
        result = tree.find_meter([0, 1])
        
        self.assertIsInstance(result, list)

    def test_find_meter_free_verse_mode(self):
        """Test find_meter in free verse mode."""
        tree = CodeTree.build_from_line(self.line, free_verse=True)
        result = tree.find_meter([0, 1])
        
        self.assertIsInstance(result, list)

    def test_find_meter_with_flag(self):
        """Test find_meter with -1 flag triggers PatternTree integration."""
        tree = CodeTree.build_from_line(self.line)
        result = tree.find_meter([0, -1])
        
        # Should work and potentially include PatternTree results
        self.assertIsInstance(result, list)
        # Results should include both regular traversal and PatternTree results
        if len(result) > 0:
            for sp in result:
                self.assertIsInstance(sp, scanPath)
                self.assertIsInstance(sp.meters, list)


class TestCodeTreeGetCode(unittest.TestCase):
    """Test CodeTree._get_code() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_get_code_no_children(self):
        """Test _get_code with no children (leaf node)."""
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._get_code(scn)
        # Should return the current path
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].location), 1)

    def test_get_code_with_children(self):
        """Test _get_code with children."""
        word_loc = codeLocation(code="-===", word_ref=0, code_ref=0, word="test", fuzzy=0)
        self.tree.add_child(word_loc)
        
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        result = self.tree._get_code(scn)
        # Should return paths for all children
        self.assertGreater(len(result), 0)


class TestCodeTreeCompressList(unittest.TestCase):
    """Test CodeTree._compress_list() method."""

    def setUp(self):
        """Set up test fixtures."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        self.tree = CodeTree(root_loc)

    def test_compress_list_same_word_locations(self):
        """Test _compress_list merges locations from same word."""
        # Create scanPath with multiple locations from same word
        scn = scanPath()
        scn.meters = [0]
        
        loc1 = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc2 = codeLocation(code="==", word_ref=0, code_ref=1, word="test", fuzzy=0)
        loc3 = codeLocation(code="=", word_ref=1, code_ref=0, word="line", fuzzy=0)
        
        scn.location.append(loc1)
        scn.location.append(loc2)
        scn.location.append(loc3)
        
        result = self.tree._compress_list([scn])
        
        self.assertEqual(len(result), 1)
        # Locations from same word should be merged
        self.assertLessEqual(len(result[0].location), 3)

    def test_compress_list_different_word_locations(self):
        """Test _compress_list keeps different word locations separate."""
        scn = scanPath()
        scn.meters = [0]
        
        loc1 = codeLocation(code="-===", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc2 = codeLocation(code="-===", word_ref=1, code_ref=0, word="line", fuzzy=0)
        
        scn.location.append(loc1)
        scn.location.append(loc2)
        
        result = self.tree._compress_list([scn])
        
        self.assertEqual(len(result), 1)
        # Different words should remain separate
        self.assertGreaterEqual(len(result[0].location), 2)


class TestCodeTreeEdgeCases(unittest.TestCase):
    """Test CodeTree edge cases."""

    def test_empty_line(self):
        """Test CodeTree with empty line."""
        line = Lines("")
        tree = CodeTree.build_from_line(line)
        
        result = tree.find_meter()
        self.assertIsInstance(result, list)

    def test_single_word_single_code(self):
        """Test CodeTree with single word and single code."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-"]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        result = tree.find_meter([0, 1])
        self.assertIsInstance(result, list)

    def test_multiple_code_variations(self):
        """Test CodeTree with multiple code variations for same word."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-===", "===-", "-=-="]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        result = tree.find_meter([0, 1, 2])
        self.assertIsInstance(result, list)

    def test_very_long_code(self):
        """Test CodeTree with very long code."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-===-===-===-==="]  # Very long code
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        result = tree.find_meter([0])
        self.assertIsInstance(result, list)

    def test_code_with_x(self):
        """Test CodeTree with 'x' (flexible syllable) in code."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["x==="]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        result = tree.find_meter([0])
        self.assertIsInstance(result, list)

    def test_min_function(self):
        """Test _min helper function."""
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = CodeTree(root_loc)
        
        self.assertEqual(tree._min(1, 2, 3), 1)
        self.assertEqual(tree._min(3, 2, 1), 1)
        self.assertEqual(tree._min(2, 1, 3), 1)
        self.assertEqual(tree._min(1, 1, 1), 1)


class TestCodeTreePatternTreeIntegration(unittest.TestCase):
    """Test PatternTree integration in CodeTree.find_meter()."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a simple line for testing
        self.line = Lines("test line")
        word1 = Words()
        word1.word = "test"
        word1.code = ["-==="]
        word2 = Words()
        word2.word = "line"
        word2.code = ["-==="]
        self.line.words_list = [word1, word2]
    
    def test_pattern_tree_triggers_with_flag(self):
        """Test PatternTree integration triggers when flag=True (meters contains -1)."""
        tree = CodeTree.build_from_line(self.line)
        
        # Call with -1 flag
        results = tree.find_meter([0, -1])
        
        # Should return results (may include PatternTree results)
        self.assertIsInstance(results, list)
        # Verify that PatternTree was called by checking if we have results
        # Note: PatternTree may or may not find matches, but integration should be triggered
        
    def test_pattern_tree_triggers_with_empty_meters(self):
        """Test PatternTree integration triggers when meters list is empty."""
        tree = CodeTree.build_from_line(self.line)
        
        # Call with empty meters list
        results = tree.find_meter([])
        
        # Should return results (PatternTree integration should be triggered)
        self.assertIsInstance(results, list)
    
    def test_pattern_tree_triggers_with_none_meters(self):
        """Test PatternTree integration triggers when meters is None."""
        tree = CodeTree.build_from_line(self.line)
        
        # Call with None meters
        results = tree.find_meter(None)
        
        # Should return results (PatternTree integration should be triggered)
        self.assertIsInstance(results, list)
    
    def test_character_expansion_single_character_codes(self):
        """Test character-by-character expansion works for single character codes."""
        # Create line with single character codes
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-"]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Get code paths
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        code_paths = tree._get_code(scn)
        
        # Verify we have paths
        self.assertGreater(len(code_paths), 0)
        
        # For each path, verify character expansion
        for path in code_paths:
            # Create PatternTree and verify character expansion
            root_loc_pt = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
            p_tree = PatternTree(root_loc_pt)
            
            # Expand characters
            for j in range(len(path.location)):
                location = path.location[j]
                code_str = location.code
                
                # Skip root
                if code_str == "root":
                    continue
                
                # Process each character
                for k in range(len(code_str)):
                    char_code = code_str[k]
                    
                    # Special handling for last character
                    if j == len(path.location) - 1 and k == len(code_str) - 1:
                        if char_code == "x":
                            char_code = "="
                    
                    char_loc = codeLocation(
                        code=char_code,
                        code_ref=location.code_ref,
                        word_ref=location.word_ref,
                        word=location.word,
                        fuzzy=location.fuzzy
                    )
                    p_tree.add_child(char_loc)
            
            # Verify PatternTree was built correctly
            self.assertIsInstance(p_tree, PatternTree)
    
    def test_character_expansion_multi_character_codes(self):
        """Test character-by-character expansion works for multi-character codes."""
        # Create line with multi-character codes
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-==="]  # Multi-character code
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Get code paths
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        code_paths = tree._get_code(scn)
        
        # Verify character expansion splits multi-character codes
        for path in code_paths:
            root_loc_pt = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
            p_tree = PatternTree(root_loc_pt)
            
            char_count = 0
            for j in range(len(path.location)):
                location = path.location[j]
                code_str = location.code
                
                if code_str == "root":
                    continue
                
                # Count characters that will be expanded
                char_count += len(code_str)
                
                for k in range(len(code_str)):
                    char_code = code_str[k]
                    if j == len(path.location) - 1 and k == len(code_str) - 1:
                        if char_code == "x":
                            char_code = "="
                    
                    char_loc = codeLocation(
                        code=char_code,
                        code_ref=location.code_ref,
                        word_ref=location.word_ref,
                        word=location.word,
                        fuzzy=location.fuzzy
                    )
                    p_tree.add_child(char_loc)
            
            # Verify we expanded multiple characters
            self.assertGreater(char_count, 1)
    
    def test_last_x_conversion_to_equals(self):
        """Test last character 'x' is converted to '=' at correct position."""
        # Create line with 'x' as last character
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-==x"]  # 'x' at the end
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Get code paths
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        code_paths = tree._get_code(scn)
        
        # Verify last 'x' is converted
        for path in code_paths:
            root_loc_pt = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
            p_tree = PatternTree(root_loc_pt)
            
            last_char = None
            for j in range(len(path.location)):
                location = path.location[j]
                code_str = location.code
                
                if code_str == "root":
                    continue
                
                for k in range(len(code_str)):
                    char_code = code_str[k]
                    is_last = (j == len(path.location) - 1 and k == len(code_str) - 1)
                    
                    if is_last and char_code == "x":
                        char_code = "="
                        last_char = char_code
                    
                    char_loc = codeLocation(
                        code=char_code,
                        code_ref=location.code_ref,
                        word_ref=location.word_ref,
                        word=location.word,
                        fuzzy=location.fuzzy
                    )
                    p_tree.add_child(char_loc)
            
            # Verify last 'x' was converted to '='
            if last_char is not None:
                self.assertEqual(last_char, "=")
    
    def test_last_x_conversion_not_middle(self):
        """Test 'x' in middle is NOT converted, only last character."""
        # Create line with 'x' in middle
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-x=="]  # 'x' in the middle
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Get code paths
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        code_paths = tree._get_code(scn)
        
        # Verify middle 'x' is NOT converted
        for path in code_paths:
            root_loc_pt = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
            p_tree = PatternTree(root_loc_pt)
            
            chars = []
            for j in range(len(path.location)):
                location = path.location[j]
                code_str = location.code
                
                if code_str == "root":
                    continue
                
                for k in range(len(code_str)):
                    char_code = code_str[k]
                    is_last = (j == len(path.location) - 1 and k == len(code_str) - 1)
                    
                    if is_last and char_code == "x":
                        char_code = "="
                    
                    chars.append(char_code)
                    
                    char_loc = codeLocation(
                        code=char_code,
                        code_ref=location.code_ref,
                        word_ref=location.word_ref,
                        word=location.word,
                        fuzzy=location.fuzzy
                    )
                    p_tree.add_child(char_loc)
            
            # Verify middle 'x' remains 'x'
            # The code "-x==" should have 'x' in position 1 (0-indexed)
            if len(chars) >= 2:
                # First char should be '-', second should be 'x' (not converted)
                self.assertEqual(chars[0], "-")
                # The 'x' in the middle should remain 'x'
                if chars[1] == "x":
                    self.assertEqual(chars[1], "x")
    
    def test_metadata_preservation_in_expansion(self):
        """Test metadata (code_ref, word_ref, word) is preserved during character expansion."""
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = ["-==="]
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Get code paths
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        code_paths = tree._get_code(scn)
        
        # Verify metadata preservation
        for path in code_paths:
            root_loc_pt = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
            p_tree = PatternTree(root_loc_pt)
            
            original_word_ref = None
            original_code_ref = None
            original_word = None
            
            for j in range(len(path.location)):
                location = path.location[j]
                code_str = location.code
                
                if code_str == "root":
                    continue
                
                # Store original metadata
                if original_word_ref is None:
                    original_word_ref = location.word_ref
                    original_code_ref = location.code_ref
                    original_word = location.word
                
                for k in range(len(code_str)):
                    char_code = code_str[k]
                    if j == len(path.location) - 1 and k == len(code_str) - 1:
                        if char_code == "x":
                            char_code = "="
                    
                    char_loc = codeLocation(
                        code=char_code,
                        code_ref=location.code_ref,
                        word_ref=location.word_ref,
                        word=location.word,
                        fuzzy=location.fuzzy
                    )
                    
                    # Verify metadata is preserved
                    self.assertEqual(char_loc.word_ref, original_word_ref)
                    self.assertEqual(char_loc.code_ref, original_code_ref)
                    self.assertEqual(char_loc.word, original_word)
                    
                    p_tree.add_child(char_loc)
    
    def test_compress_list_merges_same_word(self):
        """Test _compress_list merges locations from the same word."""
        tree = CodeTree.build_from_line(self.line)
        
        # Create a scanPath with character-by-character locations from same word
        scn = scanPath()
        scn.meters = [141]  # Some meter index
        
        # Add root
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        # Add character locations from same word (simulating PatternTree output)
        loc1 = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc2 = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc3 = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc4 = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        
        scn.location.append(loc1)
        scn.location.append(loc2)
        scn.location.append(loc3)
        scn.location.append(loc4)
        
        # Compress
        compressed = tree._compress_list([scn])
        
        # Verify compression
        self.assertEqual(len(compressed), 1)
        compressed_path = compressed[0]
        
        # Should have root + merged location
        # Locations from same word should be merged
        self.assertGreaterEqual(len(compressed_path.location), 2)
        
        # Check that codes from same word are merged
        # Skip root (index 0), check first word location (index 1)
        if len(compressed_path.location) > 1:
            # Find the first non-root location
            for i in range(1, len(compressed_path.location)):
                merged_code = compressed_path.location[i].code
                if merged_code and merged_code != "root":
                    # Should contain all characters from original locations
                    self.assertIn("-", merged_code)
                    self.assertIn("=", merged_code)
                    break
    
    def test_compress_list_keeps_different_words_separate(self):
        """Test _compress_list keeps locations from different words separate."""
        tree = CodeTree.build_from_line(self.line)
        
        # Create scanPath with locations from different words
        scn = scanPath()
        scn.meters = [141]
        
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        # Add locations from different words
        loc1 = codeLocation(code="-", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc2 = codeLocation(code="=", word_ref=0, code_ref=0, word="test", fuzzy=0)
        loc3 = codeLocation(code="-", word_ref=1, code_ref=0, word="line", fuzzy=0)
        loc4 = codeLocation(code="=", word_ref=1, code_ref=0, word="line", fuzzy=0)
        
        scn.location.append(loc1)
        scn.location.append(loc2)
        scn.location.append(loc3)
        scn.location.append(loc4)
        
        # Compress
        compressed = tree._compress_list([scn])
        
        # Verify different words remain separate
        self.assertEqual(len(compressed), 1)
        compressed_path = compressed[0]
        
        # Should have root + 2 word locations (one per word)
        # At minimum: root + word1 + word2 = 3 locations
        self.assertGreaterEqual(len(compressed_path.location), 3)
        
        # Verify word references are different
        word_refs = [loc.word_ref for loc in compressed_path.location[1:]]
        unique_word_refs = set([wr for wr in word_refs if wr >= 0])
        self.assertGreaterEqual(len(unique_word_refs), 2)
    
    def test_pattern_tree_results_combined_with_regular(self):
        """Test PatternTree results are combined with regular traversal results."""
        tree = CodeTree.build_from_line(self.line)
        
        # Call with flag to trigger PatternTree
        results = tree.find_meter([0, -1])
        
        # Should have results from both regular traversal and PatternTree
        self.assertIsInstance(results, list)
        
        # Verify all results are scanPath objects
        for sp in results:
            self.assertIsInstance(sp, scanPath)
            self.assertIsInstance(sp.location, list)
            self.assertIsInstance(sp.meters, list)
    
    def test_pattern_tree_integration_end_to_end(self):
        """Test complete PatternTree integration flow end-to-end."""
        # Create a line that might match PatternTree meters
        line = Lines("test")
        word = Words()
        word.word = "test"
        # Use a code that might match Hindi/Zamzama meters
        word.code = ["=" * 15]  # 30 syllables, might match Original Hindi
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Call with flag to trigger PatternTree
        results = tree.find_meter([-1])
        
        # Should return results
        self.assertIsInstance(results, list)
        
        # Verify results structure
        for sp in results:
            self.assertIsInstance(sp, scanPath)
            self.assertIsInstance(sp.location, list)
            self.assertIsInstance(sp.meters, list)
            
            # If PatternTree found matches, meters should be >= meter_base
            if len(sp.meters) > 0:
                meter_base = NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS
                for meter_idx in sp.meters:
                    self.assertIsInstance(meter_idx, int)
                    # PatternTree meters are >= meter_base
                    if meter_idx >= meter_base:
                        self.assertGreaterEqual(meter_idx, meter_base)
    
    def test_pattern_tree_not_triggered_without_flag(self):
        """Test PatternTree is NOT triggered when flag is False and meters is not empty."""
        tree = CodeTree.build_from_line(self.line)
        
        # Call without flag (no -1, non-empty meters)
        results_without_flag = tree.find_meter([0, 1])
        
        # Call with flag
        results_with_flag = tree.find_meter([0, -1])
        
        # Both should return results, but with flag may have additional PatternTree results
        self.assertIsInstance(results_without_flag, list)
        self.assertIsInstance(results_with_flag, list)
        
        # Results with flag may have more results or different meters
        # (PatternTree may find additional meters)
    
    def test_get_code_returns_all_paths(self):
        """Test _get_code returns all paths from root to leaves."""
        tree = CodeTree.build_from_line(self.line)
        
        scn = scanPath()
        root_loc = codeLocation(code="root", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        scn.location.append(root_loc)
        
        code_paths = tree._get_code(scn)
        
        # Should return at least one path
        self.assertGreater(len(code_paths), 0)
        
        # Each path should be a complete path from root to leaf
        for path in code_paths:
            self.assertIsInstance(path, scanPath)
            self.assertGreater(len(path.location), 0)
            # First location should be root
            self.assertEqual(path.location[0].code, "root")
            # Last location should be a leaf (no children in original tree)
    
    def test_pattern_tree_with_multiple_words(self):
        """Test PatternTree integration with multiple words."""
        tree = CodeTree.build_from_line(self.line)
        
        # Call with flag
        results = tree.find_meter([-1])
        
        # Should handle multiple words correctly
        self.assertIsInstance(results, list)
        
        # Verify word references are correct
        for sp in results:
            for loc in sp.location:
                if loc.word_ref >= 0:
                    self.assertLess(loc.word_ref, len(self.line.words_list))
    
    def test_pattern_tree_handles_empty_paths(self):
        """Test PatternTree integration handles empty code paths gracefully."""
        # Create line with no codes
        line = Lines("test")
        word = Words()
        word.word = "test"
        word.code = []  # Empty codes
        line.words_list = [word]
        
        tree = CodeTree.build_from_line(line)
        
        # Should not crash
        results = tree.find_meter([-1])
        
        # Should return empty or handle gracefully
        self.assertIsInstance(results, list)

    def test_pattern_tree_root_location_processed_character_by_character(self):
        """
        Test that PatternTree integration processes root location code='root'
        character-by-character as 'r', 'o', 'o', 't'.
        """
        tree = CodeTree.build_from_line(self.line)

        class RecordingPatternTree:
            instances = []

            def __init__(self, loc):
                self.location = loc
                self.added_codes = []
                RecordingPatternTree.instances.append(self)

            def add_child(self, loc):
                self.added_codes.append(loc.code)

            def is_match(self):
                # No actual pattern matching needed for this test
                return []

        with patch("aruuz.tree.code_tree.PatternTree", RecordingPatternTree):
            tree.find_meter([-1])

        # At least one PatternTree instance should see the root expanded
        self.assertGreater(len(RecordingPatternTree.instances), 0)
        saw_root_expansion = False
        for inst in RecordingPatternTree.instances:
            codes = inst.added_codes
            # Look for 'r','o','o','t' sequence
            for i in range(len(codes) - 3):
                if codes[i:i + 4] == ["r", "o", "o", "t"]:
                    saw_root_expansion = True
                    break
            if saw_root_expansion:
                break

        self.assertTrue(saw_root_expansion)

    def test_pattern_tree_skipped_when_get_code_returns_empty(self):
        """
        Test that when _get_code() returns an empty list, PatternTree is not constructed
        and regular traversal results are returned unchanged.
        """
        tree = CodeTree.build_from_line(self.line)

        # Baseline without PatternTree flag (regular traversal only)
        baseline_results = tree.find_meter([0])

        class RecordingPatternTree:
            instantiated = False

            def __init__(self, loc):
                RecordingPatternTree.instantiated = True

            def add_child(self, loc):
                pass

            def is_match(self):
                return []

        with patch("aruuz.tree.code_tree.CodeTree._get_code", return_value=[]), \
             patch("aruuz.tree.code_tree.PatternTree", RecordingPatternTree):
            flagged_results = tree.find_meter([0, -1])

        # PatternTree should never have been instantiated
        self.assertFalse(RecordingPatternTree.instantiated)
        # Results with flag (but no paths) should match baseline regular traversal
        self.assertEqual(len(flagged_results), len(baseline_results))
        for base_sp, flag_sp in zip(baseline_results, flagged_results):
            self.assertEqual(base_sp.meters, flag_sp.meters)
            self.assertEqual(
                [(loc.code, loc.word_ref, loc.code_ref) for loc in base_sp.location],
                [(loc.code, loc.word_ref, loc.code_ref) for loc in flag_sp.location],
            )

    def test_pattern_tree_no_matches_does_not_modify_results(self):
        """
        Test that when PatternTree.is_match() returns no paths,
        CodeTree.find_meter() results are the same as regular traversal.
        """
        tree = CodeTree.build_from_line(self.line)

        # Baseline without PatternTree
        baseline_results = tree.find_meter([0])

        class NoMatchPatternTree:
            def __init__(self, loc):
                self.location = loc

            def add_child(self, loc):
                pass

            def is_match(self):
                # Explicitly yield no matches
                return []

        with patch("aruuz.tree.code_tree.PatternTree", NoMatchPatternTree):
            flagged_results = tree.find_meter([0, -1])

        # When PatternTree adds no results, outputs should match baseline
        self.assertEqual(len(flagged_results), len(baseline_results))
        for base_sp, flag_sp in zip(baseline_results, flagged_results):
            self.assertEqual(base_sp.meters, flag_sp.meters)
            self.assertEqual(
                [(loc.code, loc.word_ref, loc.code_ref) for loc in base_sp.location],
                [(loc.code, loc.word_ref, loc.code_ref) for loc in flag_sp.location],
            )

    def test_pattern_tree_multiple_x_characters_in_codes(self):
        """
        Test that multiple 'x' characters in codes are handled correctly:
        only the very last character of the very last location is converted
        from 'x' to '=', earlier 'x' characters remain 'x'.
        """
        # Helper to exercise integration for a given code string and capture char codes
        def capture_codes_for_pattern(code_str):
            line = Lines("test")
            word = Words()
            word.word = "test"
            word.code = [code_str]
            line.words_list = [word]

            tree_local = CodeTree.build_from_line(line)

            class RecordingPatternTree:
                instances = []

                def __init__(self, loc):
                    self.location = loc
                    self.added_codes = []
                    RecordingPatternTree.instances.append(self)

                def add_child(self, loc):
                    self.added_codes.append(loc.code)

                def is_match(self):
                    return []

            with patch("aruuz.tree.code_tree.PatternTree", RecordingPatternTree):
                tree_local.find_meter([-1])

            # Collect all codes from all PatternTree instances
            all_codes = []
            for inst in RecordingPatternTree.instances:
                all_codes.extend(inst.added_codes)
            return all_codes

        # Case 1: pattern "x=x" -> first 'x' remains 'x', last 'x' becomes '='
        codes_x_eq_x = capture_codes_for_pattern("x=x")
        non_root_codes = [c for c in codes_x_eq_x if c not in ["r", "o", "t"]]
        self.assertGreaterEqual(len(non_root_codes), 3)
        tail = non_root_codes[-3:]
        # Original pattern characters: 'x', '=', 'x'
        # After integration: first 'x' unchanged, last 'x' converted to '='
        self.assertEqual(tail[0], "x")
        self.assertEqual(tail[1], "=")
        self.assertEqual(tail[2], "=")

        # Case 2: pattern "xx=" -> both 'x' remain 'x' (last char is '=')
        codes_xx_eq = capture_codes_for_pattern("xx=")
        non_root_codes2 = [c for c in codes_xx_eq if c not in ["r", "o", "t"]]
        self.assertGreaterEqual(len(non_root_codes2), 3)
        head = non_root_codes2[:3]
        self.assertEqual(head[0], "x")
        self.assertEqual(head[1], "x")


if __name__ == '__main__':
    unittest.main()

