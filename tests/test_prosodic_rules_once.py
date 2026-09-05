"""Tests that prosodic rules run at most once per line (issue #10).

The rules rewrite word codes in place and are not idempotent: ataf turns the
previous word's ``-=`` into ``--x``, and a second pass would turn that into
``---x``. ``get_scansion()`` matches every line and then scans the poem again
to find the dominant bahr, so without a guard the no-match fallback reported
inflated Step 3 codes.
"""

import unittest

from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.scansion.prosodic_rules import ProsodicRules


def _codes_after_one_pass(phrase: str) -> Lines:
    """Assign codes to a phrase and apply the prosodic rules exactly once."""
    line = Lines(phrase)
    scanner = Scansion()
    for word in line.words_list:
        scanner.assign_scansion_to_word(word)
    ProsodicRules.process_al_prefix(line)
    ProsodicRules.process_izafat(line)
    ProsodicRules.process_ataf(line)
    ProsodicRules.process_word_grafting(line)
    ProsodicRules.process_final_vowel_weakening(line)
    return line


def _primary_word_codes(phrase: str):
    """Run a phrase through get_scansion() and return [(word, code), ...]."""
    scanner = Scansion()
    scanner.add_line(Lines(phrase))
    primary = scanner.get_scansion()['line_results'][0]['results'][0]
    return [(wc['word'], wc['code']) for wc in primary['word_codes']]


class TestRuleClaim(unittest.TestCase):
    """The bookkeeping that stops a rule from running twice."""

    def test_fresh_line_starts_unclaimed(self):
        line = Lines("سخن و ادب")
        self.assertEqual(line.prosodic_rules_applied, set())

    def test_claim_succeeds_once_then_fails(self):
        line = Lines("سخن و ادب")
        self.assertTrue(ProsodicRules._claim_rule(line, 'ataf'))
        self.assertFalse(ProsodicRules._claim_rule(line, 'ataf'))

    def test_rules_are_claimed_independently(self):
        line = Lines("سخن و ادب")
        self.assertTrue(ProsodicRules._claim_rule(line, 'ataf'))
        self.assertTrue(ProsodicRules._claim_rule(line, 'izafat'))

    def test_each_rule_records_itself(self):
        line = _codes_after_one_pass("سخن و ادب")
        self.assertEqual(
            line.prosodic_rules_applied,
            {'al_prefix', 'izafat', 'ataf', 'word_grafting', 'final_vowel_weakening'},
        )


class TestAtafRunsOnce(unittest.TestCase):
    """Re-applying ataf used to grow the previous word's code by one '-'."""

    def test_repeated_ataf_does_not_inflate(self):
        line = Lines("سخن و ادب")
        scanner = Scansion()
        for word in line.words_list:
            scanner.assign_scansion_to_word(word)

        ProsodicRules.process_ataf(line)
        after_first = [list(w.code) for w in line.words_list]
        self.assertEqual(line.words_list[0].code[0], "--x")

        for _ in range(4):
            ProsodicRules.process_ataf(line)
        self.assertEqual([list(w.code) for w in line.words_list], after_first)

    def test_conjunction_explanation_is_not_duplicated(self):
        codes = _primary_word_codes("سخن و ادب")
        self.assertEqual(codes[0][1], "--x")

        scanner = Scansion()
        scanner.add_line(Lines("سخن و ادب"))
        primary = scanner.get_scansion()['line_results'][0]['results'][0]
        explanation = primary['word_codes'][0]['explanation']
        self.assertEqual(explanation.count("The conjunction 'و' caused a contextual adjustment"), 1)


class TestUnmatchedPhraseCodes(unittest.TestCase):
    """The no-match fallback reads live word codes, so it exposes the bug."""

    def test_sukhan_o_adab(self):
        self.assertEqual(
            _primary_word_codes("سخن و ادب"),
            [("سخن", "--x"), ("و", ""), ("ادب", "-=")],
        )

    def test_husn_o_ishq(self):
        self.assertEqual(_primary_word_codes("حسن و عشق")[0], ("حسن", "--x"))

    def test_bahaar_o_khizaan(self):
        self.assertEqual(_primary_word_codes("بہار و خزاں")[0], ("بہار", "-=x"))

    def test_roz_o_shab(self):
        self.assertEqual(_primary_word_codes("روز و شب")[0], ("روز", "=x"))

    def test_no_meter_matched(self):
        scanner = Scansion()
        scanner.add_line(Lines("سخن و ادب"))
        primary = scanner.get_scansion()['line_results'][0]['results'][0]
        self.assertEqual(primary['meter_name'], 'No meter match found')

    def test_fallback_matches_a_single_rules_pass(self):
        line = _codes_after_one_pass("سخن و ادب")
        expected = [(w.word, w.code[0] if w.code else "-") for w in line.words_list]
        self.assertEqual(_primary_word_codes("سخن و ادب"), expected)


class TestRescanningIsStable(unittest.TestCase):
    """Scanning the same Lines more than once must not change the codes."""

    def test_get_scansion_is_repeatable(self):
        scanner = Scansion()
        scanner.add_line(Lines("سخن و ادب"))
        first = scanner.get_scansion()['line_results'][0]['results'][0]['word_codes']
        second = scanner.get_scansion()['line_results'][0]['results'][0]['word_codes']
        third = scanner.get_scansion()['line_results'][0]['results'][0]['word_codes']
        self.assertEqual(first, second)
        self.assertEqual(second, third)

    def test_match_line_to_meters_is_repeatable(self):
        line = Lines("سخن و ادب")
        scanner = Scansion()
        scanner.match_line_to_meters(line, 0)
        after_first = [list(w.code) for w in line.words_list]
        scanner.match_line_to_meters(line, 0)
        self.assertEqual([list(w.code) for w in line.words_list], after_first)

    def test_exact_then_fuzzy_pass_is_stable(self):
        # /api/islah scans one Lines with the exact path and then the fuzzy path.
        line = Lines("سخن و ادب")
        scanner = Scansion()
        scanner.add_line(line)
        scanner.fuzzy = False
        scanner.match_line_to_meters(line, 0)
        after_exact = [list(w.code) for w in line.words_list]
        scanner.scan_line_fuzzy(line, 0)
        self.assertEqual([list(w.code) for w in line.words_list], after_exact)

    def test_scan_lines_before_get_scansion_agrees(self):
        scanner = Scansion()
        scanner.add_line(Lines("سخن و ادب"))
        scanner.scan_lines()
        codes = [
            (wc['word'], wc['code'])
            for wc in scanner.get_scansion()['line_results'][0]['results'][0]['word_codes']
        ]
        self.assertEqual(codes, [("سخن", "--x"), ("و", ""), ("ادب", "-=")])


class TestMatchedLinesUnaffected(unittest.TestCase):
    """Lines that do match a bahr keep matching it."""

    def test_dominant_bahr_still_found(self):
        scanner = Scansion()
        scanner.add_line(Lines("کوئی امید بر نہیں آتی"))
        result = scanner.get_scansion()
        self.assertEqual(result['poem_dominant_bahrs'], ['خفیف مسدس مخبون محذوف مقطوع'])

    def test_dominant_bahr_survives_an_earlier_scan(self):
        scanner = Scansion()
        scanner.add_line(Lines("کوئی امید بر نہیں آتی"))
        scanner.scan_lines()
        result = scanner.get_scansion()
        self.assertEqual(result['poem_dominant_bahrs'], ['خفیف مسدس مخبون محذوف مقطوع'])


if __name__ == '__main__':
    unittest.main()
