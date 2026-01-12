"""
Unit tests for Canonical Sher to Bahr mapping.

Tests that sher (couplets) return the correct bahr name using the crunch() method.
Test data is loaded from canonical_sher_to_bahr_mapping_data.json, making it easy to add new test cases.
"""

import unittest
import json
import os
import sys

# Add parent directory to path so we can import aruuz when running tests directly
test_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(test_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from aruuz.scansion import Scansion
from aruuz.models import Lines


class TestCanonicalSherToBahrMapping(unittest.TestCase):
    """Test that sher return the correct bahr name using crunch() method."""

    @classmethod
    def setUpClass(cls):
        """Load test data from JSON file once for all tests."""
        print("\n" + "=" * 80)
        print("LOADING TEST DATA")
        print("=" * 80)
        
        # Get the path to the JSON file in the same folder as this test file
        test_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(test_dir, 'canonical_sher_to_bahr_mapping_data.json')
        
        print(f"Reading test data from: {json_path}")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                cls.test_data = json.load(f)
            print(f"[OK] Successfully loaded {len(cls.test_data)} sher entries")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Test data file not found: {json_path}\n"
                "Please ensure canonical_sher_to_bahr_mapping_data.json exists in python/tests/"
            )
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in test data file: {json_path}\n"
                f"Error: {e}"
            )
        
        if not cls.test_data:
            raise ValueError(
                f"Test data file is empty: {json_path}\n"
                "Please add at least one sher entry to the JSON file."
            )
        
        # Validate JSON structure
        print("Validating JSON structure...")
        for idx, entry in enumerate(cls.test_data):
            required_keys = ['line1', 'line2', 'expected_bahr']
            missing_keys = [key for key in required_keys if key not in entry]
            if missing_keys:
                raise ValueError(
                    f"Invalid entry at index {idx} in test data: "
                    f"missing keys: {missing_keys}"
                )
        print("[OK] All entries validated successfully")
        print("=" * 80 + "\n")

    def test_sher_bahr_detection(self):
        """Test that each sher returns the correct bahr name.
        
        This test dynamically tests all sher entries from the JSON file.
        For each sher:
        1. Scan both lines separately
        2. Collect all scanOutput objects
        3. Use crunch() to find dominant meter
        4. Assert that the dominant meter matches expected_bahr
        """
        scansion = Scansion()
        total_shers = len(self.test_data)
        passed_count = 0
        failed_count = 0
        
        print("\n" + "=" * 80)
        print(f"TESTING {total_shers} SHER ENTRIES")
        print("=" * 80 + "\n")
        
        for idx, sher_data in enumerate(self.test_data):
            sher_num = idx + 1
            line1_text = sher_data['line1']
            line2_text = sher_data['line2']
            expected_bahr = sher_data['expected_bahr']
            
            print(f"[{sher_num}/{total_shers}] Testing Sher {sher_num}")
            print("-" * 80)
            print(f"Line 1: {line1_text}")
            print(f"Line 2: {line2_text}")
            print(f"Expected Bahr: {expected_bahr}")
            print()
            
            with self.subTest(sher_index=idx, line1=line1_text):
                # Create Lines objects for both lines
                line1 = Lines(line1_text)
                line2 = Lines(line2_text)
                
                # Scan both lines
                print(f"  Scanning line 1...")
                results_line1 = scansion.match_line_to_meters(line1, 0)
                meters_line1 = [r.meter_name for r in results_line1]
                print(f"    Found {len(results_line1)} match(es): {meters_line1}")
                
                print(f"  Scanning line 2...")
                results_line2 = scansion.match_line_to_meters(line2, 1)
                meters_line2 = [r.meter_name for r in results_line2]
                print(f"    Found {len(results_line2)} match(es): {meters_line2}")
                
                # Collect all scanOutput objects from both lines
                all_results = results_line1 + results_line2
                all_meters = [r.meter_name for r in all_results]
                
                print(f"  Total matches: {len(all_results)}")
                print(f"  Unique meters: {set(all_meters)}")
                
                # Check that we got at least some results
                self.assertGreater(
                    len(all_results), 0,
                    f"Sher {sher_num}: No meter matches found for either line.\n"
                    f"Line 1: {line1_text}\n"
                    f"Line 2: {line2_text}"
                )
                
                # Use crunch() to find dominant meter
                print(f"  Applying crunch() to find dominant meter...")
                crunched_results = scansion.resolve_dominant_meter(all_results)
                
                # Check that crunch() returned results
                self.assertGreater(
                    len(crunched_results), 0,
                    f"Sher {sher_num}: crunch() returned no results.\n"
                    f"Line 1: {line1_text}\n"
                    f"Line 2: {line2_text}\n"
                    f"All results before crunch: {all_meters}"
                )
                
                # Get the dominant meter name (all results from crunch() have same meter_name)
                dominant_meter = crunched_results[0].meter_name
                print(f"  Dominant meter: {dominant_meter}")
                print(f"  Expected meter: {expected_bahr}")
                
                # Check if they match and print result
                if dominant_meter == expected_bahr:
                    print(f"  [PASS] Bahr matches expected value")
                    passed_count += 1
                else:
                    print(f"  [FAIL] Bahr mismatch")
                    print(f"    Expected: {expected_bahr}")
                    print(f"    Got:      {dominant_meter}")
                    failed_count += 1
                
                # Assert that the dominant meter matches expected bahr
                self.assertEqual(
                    dominant_meter,
                    expected_bahr,
                    f"Sher {sher_num}: Bahr mismatch.\n"
                    f"Line 1: {line1_text}\n"
                    f"Line 2: {line2_text}\n"
                    f"Expected: {expected_bahr}\n"
                    f"Got: {dominant_meter}\n"
                    f"All meters from line 1: {meters_line1}\n"
                    f"All meters from line 2: {meters_line2}"
                )
            
            print()
        
        # Print summary
        print("=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Total sher entries tested: {total_shers}")
        print(f"Passed: {passed_count}")
        print(f"Failed: {failed_count}")
        print("=" * 80 + "\n")


if __name__ == '__main__':
    # Run with verbose output
    unittest.main(verbosity=2)

