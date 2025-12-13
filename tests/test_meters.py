"""
Tests for meter definitions.

Tests meter lookup, foot name conversion, and data integrity.
"""

import unittest
from aruuz.meters import (
    NUM_METERS,
    NUM_RUBAI_METERS,
    NUM_SPECIAL_METERS,
    METERS,
    METER_NAMES,
    FEET,
    FEET_NAMES,
    RUBAI_METERS,
    RUBAI_METER_NAMES,
    SPECIAL_METERS,
    SPECIAL_METER_NAMES,
    meter_index,
    afail,
    afail_hindi,
    rukn,
    rukn_code
)


class TestMetersData(unittest.TestCase):
    """Test meter data structures."""

    def test_num_meters(self):
        """Test that we have exactly 129 regular meters."""
        self.assertEqual(NUM_METERS, 129)
        self.assertEqual(len(METERS), 129)
        self.assertEqual(len(METER_NAMES), 129)

    def test_num_rubai_meters(self):
        """Test that we have exactly 12 rubai meters."""
        self.assertEqual(NUM_RUBAI_METERS, 12)
        self.assertEqual(len(RUBAI_METERS), 12)
        self.assertEqual(len(RUBAI_METER_NAMES), 12)

    def test_num_special_meters(self):
        """Test that we have exactly 11 special meters."""
        self.assertEqual(NUM_SPECIAL_METERS, 11)
        self.assertEqual(len(SPECIAL_METERS), 11)
        self.assertEqual(len(SPECIAL_METER_NAMES), 11)

    def test_feet_data(self):
        """Test that feet and feet names arrays match."""
        self.assertEqual(len(FEET), len(FEET_NAMES))
        self.assertGreater(len(FEET), 0)

    def test_meter_names_not_empty(self):
        """Test that all meter names are non-empty."""
        for name in METER_NAMES:
            self.assertIsInstance(name, str)
            self.assertGreater(len(name), 0)

    def test_meter_patterns_not_empty(self):
        """Test that all meter patterns are non-empty."""
        for meter in METERS:
            self.assertIsInstance(meter, str)
            self.assertGreater(len(meter), 0)


class TestMeterLookup(unittest.TestCase):
    """Test meter lookup functions."""

    def test_meter_index_existing(self):
        """Test finding meter by name."""
        # Test with a known meter
        indices = meter_index("ہزج مثمن سالم")
        self.assertGreater(len(indices), 0)
        self.assertIn(0, indices)  # First meter should be at index 0

    def test_meter_index_multiple_matches(self):
        """Test finding multiple meters with same name."""
        # Some meters have duplicate names, so we should get multiple indices
        indices = meter_index("ہزج مثمن اخرب مکفوف محذوف")
        self.assertGreaterEqual(len(indices), 1)

    def test_meter_index_not_found(self):
        """Test lookup for non-existent meter."""
        indices = meter_index("Non-existent meter")
        self.assertEqual(len(indices), 0)

    def test_meter_index_all_meters(self):
        """Test that all meter names can be found."""
        for name in METER_NAMES:
            indices = meter_index(name)
            self.assertGreater(len(indices), 0, f"Meter '{name}' not found")


class TestFootConversion(unittest.TestCase):
    """Test foot name conversion functions."""

    def test_rukn_valid_code(self):
        """Test converting valid code to foot name."""
        # Test known foot codes
        self.assertEqual(rukn("==="), "مفعولن")
        self.assertEqual(rukn("==-"), "مفعول")
        self.assertEqual(rukn("=="), "فِعْلن")
        self.assertEqual(rukn("="), "فِع")

    def test_rukn_flexible_syllable(self):
        """Test that 'x' is treated as '=' in rukn conversion."""
        # 'x' should be converted to '=' for matching
        result = rukn("x")
        self.assertEqual(result, "فِع")

    def test_rukn_invalid_code(self):
        """Test converting invalid code."""
        result = rukn("invalid")
        self.assertEqual(result, "")

    def test_rukn_code_valid_name(self):
        """Test converting valid foot name to code."""
        self.assertEqual(rukn_code("مفعولن"), "===")
        self.assertEqual(rukn_code("مفعول"), "==-")
        self.assertEqual(rukn_code("فِعْلن"), "==")
        self.assertEqual(rukn_code("فِع"), "=")

    def test_rukn_code_invalid_name(self):
        """Test converting invalid foot name."""
        result = rukn_code("Invalid foot")
        self.assertEqual(result, "")

    def test_rukn_code_roundtrip(self):
        """Test that rukn and rukn_code are inverse operations."""
        for i, foot_name in enumerate(FEET_NAMES):
            code = rukn_code(foot_name)
            if code:
                # Convert back
                name = rukn(code)
                self.assertEqual(name, foot_name, 
                               f"Roundtrip failed for {foot_name} -> {code} -> {name}")


class TestAfail(unittest.TestCase):
    """Test afail (foot name) conversion."""

    def test_afail_simple_meter(self):
        """Test converting simple meter to foot names."""
        meter = "-===/-===/-===/-==="
        result = afail(meter)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        # Should contain foot names
        self.assertIn("مفعولن", result)

    def test_afail_meter_with_plus(self):
        """Test converting meter with '+' separator."""
        meter = "=-=/-===+=-=/-==="
        result = afail(meter)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_afail_empty_meter(self):
        """Test afail with empty meter."""
        result = afail("")
        self.assertEqual(result, "")

    def test_afail_hindi_valid(self):
        """Test afail_hindi with valid special meter name."""
        meter_name = "بحرِ ہندی/ متقارب مثمن مضاعف"
        result = afail_hindi(meter_name)
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)
        self.assertIn("فعلن", result)

    def test_afail_hindi_invalid(self):
        """Test afail_hindi with invalid meter name."""
        result = afail_hindi("Invalid meter")
        self.assertEqual(result, "")


class TestDataIntegrity(unittest.TestCase):
    """Test data integrity and consistency."""

    def test_all_meters_have_names(self):
        """Test that every meter has a corresponding name."""
        self.assertEqual(len(METERS), len(METER_NAMES))

    def test_all_rubai_meters_have_names(self):
        """Test that every rubai meter has a corresponding name."""
        self.assertEqual(len(RUBAI_METERS), len(RUBAI_METER_NAMES))

    def test_all_special_meters_have_names(self):
        """Test that every special meter has a corresponding name."""
        self.assertEqual(len(SPECIAL_METERS), len(SPECIAL_METER_NAMES))

    def test_feet_and_names_match(self):
        """Test that feet array and names array have same length."""
        self.assertEqual(len(FEET), len(FEET_NAMES))

    def test_special_meters_afail_count(self):
        """Test that special meters afail array matches special meters count."""
        from aruuz.meters import SPECIAL_METERS_AFAIL
        self.assertEqual(len(SPECIAL_METERS_AFAIL), NUM_SPECIAL_METERS)


if __name__ == '__main__':
    unittest.main()
