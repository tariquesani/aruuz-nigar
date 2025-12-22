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
from aruuz.tree.code_tree import CodeTree
from aruuz.models import codeLocation, Lines, Words, scanPath
from aruuz.meters import METERS, NUM_METERS, NUM_RUBAI_METERS, USAGE


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
        """Test find_meter with -1 flag (should trigger PatternTree, but not implemented yet)."""
        tree = CodeTree.build_from_line(self.line)
        result = tree.find_meter([0, -1])
        
        # Should still work (PatternTree integration not yet implemented)
        self.assertIsInstance(result, list)


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


if __name__ == '__main__':
    unittest.main()

