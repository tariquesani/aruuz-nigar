"""Word-initial ھ+ی and a final یے keep the older code and add a second reading."""

import unittest

from aruuz.models import Lines, Words
from aruuz.scansion import Scansion
from aruuz.scansion.length_scanners import length_five_scan
from aruuz.scansion.prosodic_rules import ProsodicRules


def _assigned(text: str) -> Words:
    word = Words()
    word.word = text
    word.taqti = []
    return Scansion().assign_scansion_to_word(word)


class TestDualFiveLetterReadings(unittest.TestCase):
    def test_medial_aspirate_yeh_stays_single(self):
        for word in ("اندھیرے", "دیکھیے"):
            alternates = []
            code = length_five_scan(word, alternates=alternates)
            self.assertEqual(code, "-==")
            self.assertEqual(alternates, [])

    def test_pairahan_stays_single(self):
        alternates = []
        code = length_five_scan("پیرہن", alternates=alternates)
        self.assertEqual(code, "==-")
        self.assertEqual(alternates, [])

    def test_initial_aspirate_keeps_old_code_and_adds_fallthrough(self):
        alternates = []
        code = length_five_scan("پھیلتے", alternates=alternates)
        self.assertEqual(code, "-==")
        self.assertEqual(alternates, ["=-="])

    def test_final_ye_keeps_old_code_and_adds_long_short_long(self):
        alternates = []
        code = length_five_scan("روکیے", alternates=alternates)
        self.assertEqual(code, "==-")
        self.assertEqual(alternates, ["=-="])

    def test_assigned_words_carry_both_readings(self):
        philte = _assigned("پھیلتے")
        self.assertEqual(philte.code[0], "-==")
        self.assertIn("=-=", philte.code)

        rokiye = _assigned("روکیے")
        self.assertEqual(rokiye.code, ["==-", "=-="])

    def test_sher_dominant_bahr_is_muzari(self):
        scanner = Scansion()
        scanner.add_line(Lines("ایسا نہ ہو کہ خواب ہی ہوجائے آدمی"))
        scanner.add_line(Lines("آبادیوں میں پھیلتے جنگل کو روکیے"))
        result = scanner.get_scansion()
        self.assertEqual(
            result["poem_dominant_bahrs"],
            ["مضارع مثمن اخرب مکفوف محذوف"],
        )
        for line in result["line_results"]:
            defaults = [item for item in line["results"] if item["is_default"]]
            self.assertEqual(len(defaults), 1)
            self.assertEqual(defaults[0]["meter_name"], "مضارع مثمن اخرب مکفوف محذوف")

    def test_weakening_adds_flex_for_philte_only(self):
        line = Lines("آبادیوں میں پھیلتے جنگل کو روکیے")
        scanner = Scansion()
        for word in line.words_list:
            scanner.assign_scansion_to_word(word)
        ProsodicRules.process_final_vowel_weakening(line)
        by_word = {word.word: word.code for word in line.words_list}
        self.assertIn("-==", by_word["پھیلتے"])
        self.assertIn("=-x", by_word["پھیلتے"])
        self.assertEqual(by_word["روکیے"], ["==-", "=-="])


if __name__ == "__main__":
    unittest.main()
