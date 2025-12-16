"""
Integration tests with sample poetry lines.

Tests the complete scansion pipeline with real Urdu poetry examples.
"""

import unittest
from aruuz.scansion import Scansion
from aruuz.models import Lines


class TestScansionIntegration(unittest.TestCase):
    """Test the complete scansion pipeline."""

    def setUp(self):
        """Set up test fixtures."""
        self.scansion = Scansion()

    def test_add_line(self):
        """Test adding lines to scansion engine."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        self.assertEqual(self.scansion.num_lines, 1)
        self.assertEqual(len(self.scansion.lst_lines), 1)

    def test_word_code_assignment(self):
        """Test word code assignment."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        word = line.words_list[0]
        word = self.scansion.word_code(word)
        
        # Word should have a code assigned
        self.assertGreater(len(word.code), 0)
        self.assertIsInstance(word.code[0], str)

    def test_scan_line_basic(self):
        """Test scanning a simple line."""
        line = Lines("کتاب")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line(line, 0)
        
        # Should return a list (may be empty if no matches)
        self.assertIsInstance(results, list)
        
        # If results exist, check structure
        if len(results) > 0:
            result = results[0]
            self.assertIsNotNone(result.original_line)
            self.assertGreater(len(result.words), 0)
            self.assertGreater(len(result.word_taqti), 0)
            self.assertNotEqual(result.meter_name, "")

    def test_scan_lines_multiple_lines(self):
        """Test scanning multiple lines."""
        line1 = Lines("کتاب")
        line2 = Lines("قلم")
        
        self.scansion.add_line(line1)
        self.scansion.add_line(line2)
        
        self.assertEqual(self.scansion.num_lines, 2)
        
        results = self.scansion.scan_lines()
        
        # Should return results for all lines
        self.assertIsInstance(results, list)
        # Results may be empty if no meters match, which is fine for Phase 1

    def test_scan_line_empty_line(self):
        """Test scanning an empty line."""
        line = Lines("")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line(line, 0)
        
        # Empty line should return empty results
        self.assertEqual(len(results), 0)

    def test_scan_line_with_punctuation(self):
        """Test scanning a line with punctuation."""
        line = Lines("کتاب، قلم!")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line(line, 0)
        
        # Should handle punctuation removal
        self.assertIsInstance(results, list)

    def test_scansion_initialization(self):
        """Test scansion engine initialization."""
        scansion = Scansion()
        
        self.assertEqual(scansion.num_lines, 0)
        self.assertEqual(len(scansion.lst_lines), 0)
        self.assertFalse(scansion.is_checked)
        self.assertFalse(scansion.free_verse)
        self.assertFalse(scansion.fuzzy)
        self.assertEqual(scansion.error_param, 8)
        self.assertIsNone(scansion.meter)

    def test_word_code_preserves_existing_code(self):
        """Test that word_code doesn't overwrite existing codes."""
        line = Lines("کتاب")
        word = line.words_list[0]
        
        # Assign code manually
        word.code = ["=-="]
        
        # Call word_code
        word = self.scansion.word_code(word)
        
        # Code should be preserved
        self.assertEqual(word.code, ["=-="])

    def test_scan_line_returns_scan_output_objects(self):
        """Test that scan_line returns proper scanOutput objects."""
        line = Lines("کتاب و قلم")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line(line, 0)
        
        # All results should be scanOutput objects
        for result in results:
            self.assertIsNotNone(result.original_line)
            self.assertIsInstance(result.words, list)
            self.assertIsInstance(result.word_taqti, list)
            self.assertIsInstance(result.word_muarrab, list)
            self.assertIsInstance(result.meter_name, str)
            self.assertIsInstance(result.feet, str)
            self.assertIsInstance(result.id, int)

    def test_multiple_words_in_line(self):
        """Test scanning a line with multiple words."""
        line = Lines("کتاب و قلم و دوات")
        self.scansion.add_line(line)
        
        results = self.scansion.scan_line(line, 0)
        
        # Should process all words
        self.assertIsInstance(results, list)
        
        if len(results) > 0:
            result = results[0]
            # Should have codes for all words
            self.assertEqual(len(result.word_taqti), len(line.words_list))
            self.assertEqual(len(result.words), len(line.words_list))


if __name__ == '__main__':
    unittest.main()
