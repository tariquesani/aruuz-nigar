"""Tests for aruuz.utils.aligner (standalone align function)."""

import unittest
from aruuz.utils.aligner import align, match_char


class TestMatchChar(unittest.TestCase):
    def test_exact(self):
        self.assertTrue(match_char("-", "-"))
        self.assertTrue(match_char("=", "="))

    def test_x_wildcard(self):
        self.assertTrue(match_char("-", "x"))
        self.assertTrue(match_char("=", "x"))
        self.assertFalse(match_char("~", "x"))

    def test_tilde(self):
        self.assertTrue(match_char("~", "-"))
        self.assertFalse(match_char("~", "="))


class TestAlign(unittest.TestCase):
    def test_distance_matches_levenshtein(self):
        from aruuz.models import codeLocation
        from aruuz.tree.code_tree import CodeTree

        loc = codeLocation(code="", word_ref=-1, code_ref=-1, word="", fuzzy=0)
        tree = CodeTree(loc)

        pairs = [
            ("-===", "-==="),
            ("-===", "-=x="),
            ("-===", "===="),
            ("-~==", "--=="),
            ("=", ""),
            ("", "="),
        ]
        for pattern, code in pairs:
            lev = tree._levenshtein_distance(pattern, code)
            dist, _, _ = align(pattern, code)
            self.assertEqual(lev, dist, f"pattern={pattern!r} code={code!r}")

    def test_full_match(self):
        dist, ops, leverage = align("-===", "-===")
        self.assertEqual(dist, 0)
        self.assertEqual(len(ops), 4)
        self.assertTrue(all(o["op"] == "match" for o in ops))
        self.assertEqual(leverage, [(0, 4)])

    def test_one_substitute(self):
        dist, ops, leverage = align("-===", "====")
        self.assertEqual(dist, 1)
        subs = [o for o in ops if o["op"] == "substitute"]
        self.assertEqual(len(subs), 1)
        self.assertEqual(subs[0]["pattern_pos"], 0)
        self.assertEqual(subs[0]["code_pos"], 0)
        self.assertEqual(leverage, [(1, 4)])

    def test_insert_delete(self):
        dist, ops, _ = align("=", "")
        self.assertEqual(dist, 1)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]["op"], "insert")

        dist, ops, _ = align("", "=")
        self.assertEqual(dist, 1)
        self.assertEqual(len(ops), 1)
        self.assertEqual(ops[0]["op"], "delete")
