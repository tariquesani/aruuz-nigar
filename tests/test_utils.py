"""
Tests for utility functions.
"""

import unittest

from aruuz.utils.araab import remove_araab


class TestAraabUtils(unittest.TestCase):
    def test_remove_araab_removes_known_marks(self):
        # Arabic diacritics: shadd (\u0651), zabar (\u064E), paish (\u064F)
        word = "کَتّابٌ"  # contains zabar, shadd, paish
        expected = "کتاب"
        self.assertEqual(remove_araab(word), expected)

    def test_remove_araab_empty_and_none(self):
        self.assertEqual(remove_araab(""), "")
        self.assertEqual(remove_araab(None), "")

    def test_remove_araab_no_diacritics(self):
        word = "کتاب"
        self.assertEqual(remove_araab(word), word)


if __name__ == "__main__":
    unittest.main()