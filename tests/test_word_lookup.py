"""
Comprehensive tests for WordLookup.find_word() method.

Tests database lookups in:
- exceptions table
- mastertable (with variations " 1" through " 12")
- plurals table
- variations table

Verifies all field mappings (id, code, taqti, muarrab, language, is_varied),
error handling, and compares results with C# findWord() behavior.
"""

import unittest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from aruuz.database.word_lookup import WordLookup
from aruuz.models import Words
from aruuz.utils.araab import remove_araab


class TestWordLookupExceptionsTable(unittest.TestCase):
    """Test find_word() lookup in exceptions table."""

    def setUp(self):
        """Set up test database with exceptions table."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create exceptions table matching C# schema
        # C#: id, Word, Taqti, Taqti2, Taqti3
        self.cursor.execute("""
            CREATE TABLE exceptions (
                id INTEGER PRIMARY KEY,
                word TEXT,
                Taqti TEXT,
                Taqti2 TEXT,
                Taqti3 TEXT
            )
        """)
        
        # Insert test data
        self.cursor.execute("""
            INSERT INTO exceptions (id, word, Taqti, Taqti2, Taqti3)
            VALUES (1, 'testword', '= -', '= =', '= - =')
        """)
        
        # Word with only Taqti (no Taqti2, Taqti3)
        self.cursor.execute("""
            INSERT INTO exceptions (id, word, Taqti, Taqti2, Taqti3)
            VALUES (2, 'singleword', '= - =', NULL, NULL)
        """)
        
        # Word with Taqti and Taqti2 (no Taqti3)
        self.cursor.execute("""
            INSERT INTO exceptions (id, word, Taqti, Taqti2, Taqti3)
            VALUES (3, 'doubleword', '= -', '= =', NULL)
        """)
        
        self.conn.commit()
        self.conn.close()
        
        # Create WordLookup instance with test database
        self.word_lookup = WordLookup(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_exceptions_table_single_taqti(self):
        """Test exceptions table lookup with single Taqti (no Taqti2, Taqti3).
        
        C# behavior: wrd.id.Add(dataReader.GetInt32(0)*-1)
        C# behavior: wrd.code.Add(dataReader.GetString(2).Replace(" ", ""))
        """
        word = Words()
        word.word = 'singleword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id is negative (C#: id * -1)
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], -2)  # id=2, so -2
        
        # Verify code has spaces removed
        self.assertEqual(len(result.code), 1)
        self.assertEqual(result.code[0], '=-=')  # '= - =' with spaces removed
        
        # Verify word is unchanged
        self.assertEqual(result.word, 'singleword')

    def test_exceptions_table_multiple_taqti(self):
        """Test exceptions table lookup with Taqti, Taqti2, Taqti3.
        
        C# behavior: Adds all non-empty taqti values to code list
        """
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id is negative
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], -1)  # id=1, so -1
        
        # Verify all three codes are added (spaces removed)
        self.assertEqual(len(result.code), 3)
        self.assertEqual(result.code[0], '=-')   # Taqti: '= -' -> '=-'
        self.assertEqual(result.code[1], '==')   # Taqti2: '= =' -> '=='
        self.assertEqual(result.code[2], '=-=')   # Taqti3: '= - =' -> '=-='
        
        # Verify word is unchanged
        self.assertEqual(result.word, 'testword')

    def test_exceptions_table_two_taqti(self):
        """Test exceptions table lookup with Taqti and Taqti2 (no Taqti3).
        
        C# behavior: Only adds non-empty taqti values
        """
        word = Words()
        word.word = 'doubleword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id is negative
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], -3)  # id=3, so -3
        
        # Verify only two codes are added
        self.assertEqual(len(result.code), 2)
        self.assertEqual(result.code[0], '=-')   # Taqti: '= -' -> '=-'
        self.assertEqual(result.code[1], '==')    # Taqti2: '= =' -> '=='
        
        # Verify word is unchanged
        self.assertEqual(result.word, 'doubleword')

    def test_exceptions_table_araab_removal(self):
        """Test that araab is removed before searching.
        
        C# behavior: string searchWord = Araab.removeAraab(wrd.word);
        """
        word = Words()
        # Word with diacritics - should match 'testword' after araab removal
        word.word = 'testword\u064E'  # testword with zabar
        
        result = self.word_lookup.find_word(word)
        
        # Should find the word in exceptions table
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], -1)

    def test_exceptions_table_not_found(self):
        """Test exceptions table lookup when word is not found.
        
        Should proceed to mastertable lookup (not return early).
        """
        word = Words()
        word.word = 'nonexistentword'
        
        result = self.word_lookup.find_word(word)
        
        # Should not find in exceptions, so id should be empty
        # (will try other tables, but for this test we only have exceptions table)
        # Since we don't have other tables, id will be empty
        self.assertEqual(len(result.id), 0)


class TestWordLookupMastertable(unittest.TestCase):
    """Test find_word() lookup in mastertable with variations."""

    def setUp(self):
        """Set up test database with mastertable."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create mastertable matching C# schema
        # C#: ID, Word, Muarrab, Taqti, Language, isVaried, isPlural
        self.cursor.execute("""
            CREATE TABLE mastertable (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER,
                isPlural INTEGER
            )
        """)
        
        # Insert test data - base word
        self.cursor.execute("""
            INSERT INTO mastertable (ID, word, Muarrab, Taqti, Language, isVaried, isPlural)
            VALUES (1, 'testword', 'testword\u064E', '= - =', 'ur', 0, 0)
        """)
        
        # Insert test data - word with variation " 1"
        self.cursor.execute("""
            INSERT INTO mastertable (ID, word, Muarrab, Taqti, Language, isVaried, isPlural)
            VALUES (2, 'testword 1', 'testword\u0650', '= =', 'ur', 0, 0)
        """)
        
        # Insert test data - word with isVaried=1 (should trigger variations table lookup)
        self.cursor.execute("""
            INSERT INTO mastertable (ID, word, Muarrab, Taqti, Language, isVaried, isPlural)
            VALUES (3, 'variedword', 'variedword\u064E', '= -', 'ur', 1, 0)
        """)
        
        # Insert test data - word with NULL language (should handle gracefully)
        self.cursor.execute("""
            INSERT INTO mastertable (ID, word, Muarrab, Taqti, Language, isVaried, isPlural)
            VALUES (4, 'nullword', 'nullword\u064E', '= - =', NULL, 0, 0)
        """)
        
        self.conn.commit()
        self.conn.close()
        
        # Create WordLookup instance with test database
        self.word_lookup = WordLookup(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_mastertable_base_word(self):
        """Test mastertable lookup with base word (no variation).
        
        C# behavior:
        - wrd.id.Add(dataReader2.GetInt32(0))
        - wrd.muarrab.Add(dataReader2.GetString(2).Trim())
        - wrd.taqti.Add(dataReader2.GetString(3).Trim())
        - wrd.language.Add(dataReader2.GetString(4)) (with try/catch)
        - wrd.isVaried.Add(dataReader2.GetBoolean(5))
        - wrd.code.Add(assignCode(wrd))
        """
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 1)  # Positive id (not negative like exceptions)
        
        # Verify muarrab (trimmed)
        self.assertEqual(len(result.muarrab), 1)
        self.assertEqual(result.muarrab[0], 'testword\u064E')
        
        # Verify taqti (trimmed)
        self.assertEqual(len(result.taqti), 1)
        self.assertEqual(result.taqti[0], '= - =')
        
        # Verify language
        self.assertEqual(len(result.language), 1)
        self.assertEqual(result.language[0], 'ur')
        
        # Verify is_varied
        self.assertEqual(len(result.is_varied), 1)
        self.assertFalse(result.is_varied[0])
        
        # Verify code (assigned via assign_code)
        self.assertEqual(len(result.code), 1)
        self.assertIsInstance(result.code[0], str)
        self.assertGreater(len(result.code[0]), 0)

    def test_mastertable_with_variation(self):
        """Test mastertable lookup with variation " 1".
        
        C# behavior: Searches for base word + " 1" through " 12"
        """
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find both base word and variation " 1"
        # Note: C# finds all matching rows, so we might get multiple results
        self.assertGreaterEqual(len(result.id), 1)
        
        # Check that we found at least the base word
        self.assertIn(1, result.id)

    def test_mastertable_is_varied_true(self):
        """Test mastertable lookup with isVaried=True triggers variations table lookup.
        
        C# behavior:
        if (wrd.isVaried.Count > 0) {
            if (wrd.isVaried[0]) {
                // Query variations table by id (using wrd.id[0])
            }
        }
        """
        # Create variations table for this test
        # Note: C# uses lowercase 'variations' for this query
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE variations (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER
            )
        """)
        # Insert variation for id=3 (matching mastertable entry)
        # C# queries: "select * from variations where id = @id;"
        # Uses wrd.id[0] as the id parameter (which will be 3 from mastertable)
        cursor.execute("""
            INSERT INTO variations (ID, word, Muarrab, Taqti, Language, isVaried)
            VALUES (3, 'variedword_var', 'variedword_var\u064E', '= =', 'ur', 0)
        """)
        conn.commit()
        conn.close()
        
        word = Words()
        word.word = 'variedword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find in mastertable first (id=3)
        self.assertGreaterEqual(len(result.id), 1)
        self.assertIn(3, result.id)
        
        # Should also find in variations table
        # C# queries variations table by id using wrd.id[0] (which is 3)
        # The variation with id=3 should be found and added to the result
        # So we should have at least 2 entries in id list (mastertable entry + variation)
        self.assertGreaterEqual(len(result.id), 2, "Should find mastertable entry and variation")
        
        # Both entries should have id=3 (mastertable and variation both have id=3)
        # Actually, wait - the variation table entry has its own ID, which is also 3
        # So we'll have id=[3, 3] - one from mastertable, one from variations
        self.assertEqual(result.id.count(3), 2, "Should have two entries with id=3")
        
        # Verify is_varied is True for first entry
        if len(result.is_varied) > 0:
            self.assertTrue(result.is_varied[0])
        
        # Verify we have codes for both entries
        self.assertEqual(len(result.code), 2, "Should have codes for mastertable and variation")

    def test_mastertable_null_language(self):
        """Test mastertable lookup with NULL language field.
        
        C# behavior: try { wrd.language.Add(dataReader2.GetString(4)); } catch {}
        """
        word = Words()
        word.word = 'nullword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find the word
        self.assertGreaterEqual(len(result.id), 1)
        self.assertIn(4, result.id)
        
        # Language should be empty string if NULL (handled gracefully)
        # C# catches exception and doesn't add, but Python adds empty string
        self.assertEqual(len(result.language), len(result.id))
        # At least one language entry should exist (may be empty string)

    def test_mastertable_not_found(self):
        """Test mastertable lookup when word is not found.
        
        Should proceed to plurals table lookup.
        """
        word = Words()
        word.word = 'nonexistentword'
        
        result = self.word_lookup.find_word(word)
        
        # Should not find in mastertable
        self.assertEqual(len(result.id), 0)


class TestWordLookupPluralsTable(unittest.TestCase):
    """Test find_word() lookup in Plurals table."""

    def setUp(self):
        """Set up test database with Plurals table."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create Plurals table (capitalized, matching C#)
        # C#: "select * from Plurals where word like @s;"
        self.cursor.execute("""
            CREATE TABLE Plurals (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER
            )
        """)
        
        # Insert test data
        self.cursor.execute("""
            INSERT INTO Plurals (ID, word, Muarrab, Taqti, Language, isVaried)
            VALUES (1, 'pluralword', 'pluralword\u064E', '= - =', 'ur', 0)
        """)
        
        self.conn.commit()
        self.conn.close()
        
        # Create WordLookup instance with test database
        self.word_lookup = WordLookup(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_plurals_table_lookup(self):
        """Test Plurals table lookup.
        
        C# behavior:
        - Only checked if mastertable lookup fails
        - wrd.id.Add(dataReader3.GetInt32(0))
        - wrd.muarrab.Add(dataReader3.GetString(2).Trim())
        - wrd.taqti.Add(dataReader3.GetString(3).Trim())
        - wrd.code.Add(assignCode(wrd))
        """
        word = Words()
        word.word = 'pluralword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 1)
        
        # Verify muarrab (trimmed)
        self.assertEqual(len(result.muarrab), 1)
        self.assertEqual(result.muarrab[0], 'pluralword\u064E')
        
        # Verify taqti (trimmed)
        self.assertEqual(len(result.taqti), 1)
        self.assertEqual(result.taqti[0], '= - =')
        
        # Verify code (assigned via assign_code)
        self.assertEqual(len(result.code), 1)
        self.assertIsInstance(result.code[0], str)
        self.assertGreater(len(result.code[0]), 0)

    def test_plurals_table_not_found(self):
        """Test Plurals table lookup when word is not found.
        
        Should proceed to Variations table lookup.
        """
        word = Words()
        word.word = 'nonexistentword'
        
        result = self.word_lookup.find_word(word)
        
        # Should not find in Plurals
        self.assertEqual(len(result.id), 0)


class TestWordLookupVariationsTable(unittest.TestCase):
    """Test find_word() lookup in Variations table."""

    def setUp(self):
        """Set up test database with Variations table."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create Variations table (capitalized, matching C#)
        # C#: "select * from Variations where word like @s;"
        self.cursor.execute("""
            CREATE TABLE Variations (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER
            )
        """)
        
        # Insert test data
        self.cursor.execute("""
            INSERT INTO Variations (ID, word, Muarrab, Taqti, Language, isVaried)
            VALUES (1, 'variationword', 'variationword\u064E', '= - =', 'ur', 0)
        """)
        
        self.conn.commit()
        self.conn.close()
        
        # Create WordLookup instance with test database
        self.word_lookup = WordLookup(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_variations_table_lookup(self):
        """Test Variations table lookup.
        
        C# behavior:
        - Only checked if Plurals lookup fails
        - wrd.id.Add(dataReader4.GetInt32(0))
        - wrd.muarrab.Add(dataReader4.GetString(2).Trim())
        - wrd.taqti.Add(dataReader4.GetString(3).Trim())
        - wrd.code.Add(assignCode(wrd))
        """
        word = Words()
        word.word = 'variationword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 1)
        
        # Verify muarrab (trimmed)
        self.assertEqual(len(result.muarrab), 1)
        self.assertEqual(result.muarrab[0], 'variationword\u064E')
        
        # Verify taqti (trimmed)
        self.assertEqual(len(result.taqti), 1)
        self.assertEqual(result.taqti[0], '= - =')
        
        # Verify code (assigned via assign_code)
        self.assertEqual(len(result.code), 1)
        self.assertIsInstance(result.code[0], str)
        self.assertGreater(len(result.code[0]), 0)

    def test_variations_table_not_found(self):
        """Test Variations table lookup when word is not found.
        
        Should return word with empty id list.
        """
        word = Words()
        word.word = 'nonexistentword'
        
        result = self.word_lookup.find_word(word)
        
        # Should not find in Variations
        self.assertEqual(len(result.id), 0)


class TestWordLookupLookupOrder(unittest.TestCase):
    """Test that find_word() follows correct lookup order (exceptions -> mastertable -> plurals -> variations)."""

    def setUp(self):
        """Set up test database with all tables."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create all tables
        self.cursor.execute("""
            CREATE TABLE exceptions (
                id INTEGER PRIMARY KEY,
                word TEXT,
                Taqti TEXT,
                Taqti2 TEXT,
                Taqti3 TEXT
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE mastertable (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER,
                isPlural INTEGER
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE Plurals (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE Variations (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER
            )
        """)
        
        # Insert same word in all tables (to test lookup order)
        self.cursor.execute("""
            INSERT INTO exceptions (id, word, Taqti, Taqti2, Taqti3)
            VALUES (1, 'testword', '= -', NULL, NULL)
        """)
        
        self.cursor.execute("""
            INSERT INTO mastertable (ID, word, Muarrab, Taqti, Language, isVaried, isPlural)
            VALUES (2, 'testword', 'testword\u064E', '= =', 'ur', 0, 0)
        """)
        
        self.cursor.execute("""
            INSERT INTO Plurals (ID, word, Muarrab, Taqti, Language, isVaried)
            VALUES (3, 'testword', 'testword\u064E', '= = =', 'ur', 0)
        """)
        
        self.cursor.execute("""
            INSERT INTO Variations (ID, word, Muarrab, Taqti, Language, isVaried)
            VALUES (4, 'testword', 'testword\u064E', '= = = =', 'ur', 0)
        """)
        
        self.conn.commit()
        self.conn.close()
        
        # Create WordLookup instance with test database
        self.word_lookup = WordLookup(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_lookup_order_exceptions_first(self):
        """Test that exceptions table is checked first.
        
        C# behavior: Exceptions table is checked first, returns early if found.
        """
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find in exceptions table (returns early, doesn't check other tables)
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], -1)  # Negative id indicates exceptions table
        
        # Should have code from exceptions table
        self.assertEqual(len(result.code), 1)
        self.assertEqual(result.code[0], '=-')  # From exceptions Taqti

    def test_lookup_order_mastertable_second(self):
        """Test that mastertable is checked second (if exceptions not found).
        
        C# behavior: If exceptions not found, checks mastertable.
        """
        # Remove word from exceptions table
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM exceptions WHERE word = 'testword'")
        conn.commit()
        conn.close()
        
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find in mastertable (not exceptions)
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 2)  # Positive id from mastertable
        
        # Should have code from mastertable (via assign_code)
        self.assertEqual(len(result.code), 1)

    def test_lookup_order_plurals_third(self):
        """Test that Plurals table is checked third (if mastertable not found).
        
        C# behavior: If mastertable not found, checks Plurals.
        """
        # Remove word from exceptions and mastertable
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM exceptions WHERE word = 'testword'")
        cursor.execute("DELETE FROM mastertable WHERE word = 'testword'")
        conn.commit()
        conn.close()
        
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find in Plurals table
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 3)  # Positive id from Plurals
        
        # Should have code from Plurals (via assign_code)
        self.assertEqual(len(result.code), 1)

    def test_lookup_order_variations_fourth(self):
        """Test that Variations table is checked fourth (if Plurals not found).
        
        C# behavior: If Plurals not found, checks Variations.
        """
        # Remove word from exceptions, mastertable, and Plurals
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM exceptions WHERE word = 'testword'")
        cursor.execute("DELETE FROM mastertable WHERE word = 'testword'")
        cursor.execute("DELETE FROM Plurals WHERE word = 'testword'")
        conn.commit()
        conn.close()
        
        word = Words()
        word.word = 'testword'
        
        result = self.word_lookup.find_word(word)
        
        # Should find in Variations table
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 4)  # Positive id from Variations
        
        # Should have code from Variations (via assign_code)
        self.assertEqual(len(result.code), 1)


class TestWordLookupErrorHandling(unittest.TestCase):
    """Test error handling in find_word()."""

    def test_database_file_not_found(self):
        """Test error handling when database file doesn't exist."""
        # Use non-existent database path
        word_lookup = WordLookup(db_path='/nonexistent/path/to/database.db')
        
        word = Words()
        word.word = 'testword'
        
        # Should raise an error when trying to connect
        with self.assertRaises((sqlite3.OperationalError, FileNotFoundError)):
            word_lookup.find_word(word)

    def test_database_connection_error(self):
        """Test error handling when database connection fails."""
        # This is harder to test without mocking, but we can test with invalid path
        word_lookup = WordLookup(db_path=':memory:')  # In-memory DB should work
        
        word = Words()
        word.word = 'testword'
        
        # Should handle gracefully (return word with empty id)
        result = word_lookup.find_word(word)
        self.assertEqual(len(result.id), 0)

    def test_empty_word(self):
        """Test handling of empty word."""
        # Create minimal database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        conn = sqlite3.connect(db_path)
        conn.close()
        
        word_lookup = WordLookup(db_path=db_path)
        
        word = Words()
        word.word = ''
        
        # Should handle gracefully
        result = word_lookup.find_word(word)
        self.assertEqual(len(result.id), 0)
        
        os.close(db_fd)
        os.unlink(db_path)

    def test_word_with_special_characters(self):
        """Test handling of words with special characters."""
        # Create minimal database
        db_fd, db_path = tempfile.mkstemp(suffix='.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE exceptions (
                id INTEGER PRIMARY KEY,
                word TEXT,
                Taqti TEXT
            )
        """)
        conn.commit()
        conn.close()
        
        word_lookup = WordLookup(db_path=db_path)
        
        # Test with various special characters
        test_words = [
            'word\u064E',  # with zabar
            'word\u0650',  # with zer
            'word\u0652',  # with jazm
            'word\u0651',  # with shadd
        ]
        
        for test_word in test_words:
            with self.subTest(word=test_word):
                word = Words()
                word.word = test_word
                result = word_lookup.find_word(word)
                # Should not raise exception
                self.assertIsInstance(result, Words)
        
        os.close(db_fd)
        os.unlink(db_path)


class TestWordLookupFieldMappings(unittest.TestCase):
    """Test that all field mappings are correct (id, code, taqti, muarrab, language, is_varied)."""

    def setUp(self):
        """Set up comprehensive test database."""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create mastertable with all fields populated
        self.cursor.execute("""
            CREATE TABLE mastertable (
                ID INTEGER PRIMARY KEY,
                word TEXT,
                Muarrab TEXT,
                Taqti TEXT,
                Language TEXT,
                isVaried INTEGER,
                isPlural INTEGER
            )
        """)
        
        # Insert comprehensive test data
        self.cursor.execute("""
            INSERT INTO mastertable (ID, word, Muarrab, Taqti, Language, isVaried, isPlural)
            VALUES (100, 'completestword', 'completestword\u064E\u0650', '= - = -', 'ur', 1, 0)
        """)
        
        self.conn.commit()
        self.conn.close()
        
        # Create WordLookup instance
        self.word_lookup = WordLookup(db_path=self.db_path)

    def tearDown(self):
        """Clean up test database."""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_all_fields_populated(self):
        """Test that all fields are correctly populated from database.
        
        Verifies:
        - id: Positive integer from database
        - muarrab: Trimmed string from Muarrab column
        - taqti: Trimmed string from Taqti column
        - language: String from Language column
        - is_varied: Boolean from isVaried column
        - code: Generated via assign_code() using taqti
        """
        word = Words()
        word.word = 'completestword'
        
        result = self.word_lookup.find_word(word)
        
        # Verify id
        self.assertEqual(len(result.id), 1)
        self.assertEqual(result.id[0], 100)
        self.assertIsInstance(result.id[0], int)
        
        # Verify muarrab (trimmed)
        self.assertEqual(len(result.muarrab), 1)
        self.assertEqual(result.muarrab[0], 'completestword\u064E\u0650')
        self.assertIsInstance(result.muarrab[0], str)
        
        # Verify taqti (trimmed)
        self.assertEqual(len(result.taqti), 1)
        self.assertEqual(result.taqti[0], '= - = -')
        self.assertIsInstance(result.taqti[0], str)
        
        # Verify language
        self.assertEqual(len(result.language), 1)
        self.assertEqual(result.language[0], 'ur')
        self.assertIsInstance(result.language[0], str)
        
        # Verify is_varied (boolean)
        self.assertEqual(len(result.is_varied), 1)
        self.assertTrue(result.is_varied[0])
        self.assertIsInstance(result.is_varied[0], bool)
        
        # Verify code (generated via assign_code)
        self.assertEqual(len(result.code), 1)
        self.assertIsInstance(result.code[0], str)
        self.assertGreater(len(result.code[0]), 0)

    def test_field_list_lengths_match(self):
        """Test that all field lists have the same length (one entry per database row)."""
        word = Words()
        word.word = 'completestword'
        
        result = self.word_lookup.find_word(word)
        
        # All lists should have the same length
        list_length = len(result.id)
        self.assertEqual(len(result.muarrab), list_length)
        self.assertEqual(len(result.taqti), list_length)
        self.assertEqual(len(result.language), list_length)
        self.assertEqual(len(result.is_varied), list_length)
        self.assertEqual(len(result.code), list_length)


class TestWordLookupRealDatabase(unittest.TestCase):
    """Test find_word() with real database if available (for comparison with C#)."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test with real database if available."""
        try:
            from aruuz.database.config import get_db_path
            cls.db_path = get_db_path()
            cls.real_db_available = os.path.exists(cls.db_path)
        except (FileNotFoundError, ImportError):
            cls.real_db_available = False
            cls.db_path = None
    
    def setUp(self):
        """Set up WordLookup with real database if available."""
        if not self.real_db_available:
            self.skipTest("Real database not available for comparison testing")
        
        self.word_lookup = WordLookup(db_path=self.db_path)
    
    def test_real_database_connection(self):
        """Test that we can connect to the real database."""
        # Just verify connection works
        word = Words()
        word.word = 'test'
        result = self.word_lookup.find_word(word)
        # Should not raise exception
        self.assertIsInstance(result, Words)
    
    def test_real_database_exceptions_table(self):
        """Test exceptions table lookup with real database.
        
        This test can be used to compare Python results with C# findWord() results
        for the same input words.
        """
        # Try to find a word that might be in exceptions table
        # Note: This depends on actual database content
        word = Words()
        word.word = 'کتاب'  # Common Urdu word
        
        result = self.word_lookup.find_word(word)
        
        # Verify structure is correct (regardless of whether word is found)
        self.assertIsInstance(result, Words)
        self.assertEqual(result.word, 'کتاب')
        
        # If found, verify field mappings
        if len(result.id) > 0:
            # If found in exceptions, id should be negative
            if result.id[0] < 0:
                # Should have at least one code
                self.assertGreater(len(result.code), 0)
                # All codes should be strings
                for code in result.code:
                    self.assertIsInstance(code, str)
    
    def test_real_database_mastertable(self):
        """Test mastertable lookup with real database.
        
        This test can be used to compare Python results with C# findWord() results.
        """
        word = Words()
        word.word = 'دل'  # Common Urdu word
        
        result = self.word_lookup.find_word(word)
        
        # Verify structure is correct
        self.assertIsInstance(result, Words)
        self.assertEqual(result.word, 'دل')
        
        # If found, verify field mappings
        if len(result.id) > 0:
            # If found in mastertable, id should be positive
            if result.id[0] > 0:
                # Should have muarrab, taqti, code
                self.assertEqual(len(result.muarrab), len(result.id))
                self.assertEqual(len(result.taqti), len(result.id))
                self.assertEqual(len(result.code), len(result.id))
                # All muarrab and taqti should be strings
                for muarrab in result.muarrab:
                    self.assertIsInstance(muarrab, str)
                for taqti in result.taqti:
                    self.assertIsInstance(taqti, str)
                for code in result.code:
                    self.assertIsInstance(code, str)


if __name__ == '__main__':
    unittest.main()

