"""
Tests for Bahr (meter) detection.

Tests that specific poetry lines return the expected Bahr names
and that line-level ambiguity collapses correctly at sher level.
"""

import unittest
from aruuz.scansion import Scansion
from aruuz.models import Lines


class TestBahrDetection(unittest.TestCase):
    """Test Bahr (meter) detection for specific poetry lines."""

    def test_line1_bahr_unambiguous(self):
        """Line 1 should be metrically unambiguous.

        دم اندھیرے میں گھٹ رہا ہے خمار
        → خفیف مسدس مخبون محذوف
        """
        scansion = Scansion()
        line_text = "دم اندھیرے میں گھٹ رہا ہے خمار"
        line = Lines(line_text)

        results = scansion.scan_line(line, 0)
        self.assertGreater(len(results), 0,
                           f"No meter matches found for line: {line_text}")

        meter_names = {r.meter_name for r in results}
        self.assertEqual(
            meter_names,
            {"خفیف مسدس مخبون محذوف"},
            f"Line should be unambiguous, got meters: {meter_names}"
        )

    def test_line2_bahr_ambiguous_but_bounded(self):
        """Line 2 should return exactly two Bahrs.

        اور چاروں طرف اجالا ہے
        →
        - خفیف مسدس مخبون محذوف مقطوع
        - خفیف مسدس سالم مخبون محجوف
        """
        scansion = Scansion()
        line_text = "اور چاروں طرف اجالا ہے"
        line = Lines(line_text)

        results = scansion.scan_line(line, 0)
        self.assertGreater(len(results), 0,
                           f"No meter matches found for line: {line_text}")

        meter_names = {r.meter_name for r in results}
        expected = {
            "خفیف مسدس مخبون محذوف مقطوع",
            "خفیف مسدس سالم مخبون محجوف",
        }

        self.assertEqual(
            meter_names,
            expected,
            f"Line should return exactly {expected}, got {meter_names}"
        )


class TestSherBahrIntersection(unittest.TestCase):
    """Test Bahr reconciliation across a full sher."""

    @unittest.expectedFailure
    def test_sher_bahr_intersection(self):
        """
        Expected failure until Bahr canonicalization is implemented.

        Currently, meter names are treated as atomic strings.
        Bahr families (e.g. خفیف مسدس مخبون) are not yet normalized,
        so zihaf variants do not intersect by name.
        """
        scansion = Scansion()

        line1 = Lines("دم اندھیرے میں گھٹ رہا ہے خمار")
        line2 = Lines("اور چاروں طرف اجالا ہے")

        bahrs1 = {r.meter_name for r in scansion.scan_line(line1, 0)}
        bahrs2 = {r.meter_name for r in scansion.scan_line(line2, 0)}

        self.assertEqual(len(bahrs1), 1)
        self.assertGreater(len(bahrs2), 1)

        self.assertEqual(
            bahrs1 & bahrs2,
            bahrs1,
            f"Sher Bahr mismatch: line1={bahrs1}, line2={bahrs2}"
        )



if __name__ == '__main__':
    unittest.main()
