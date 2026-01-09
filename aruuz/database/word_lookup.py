"""
Database word lookup module for Aruuz.

Provides WordLookup class for querying SQLite database to find word scansion information.
"""

import logging
import sqlite3
from typing import Optional
from aruuz.models import Words
from aruuz.utils.araab import remove_araab
from aruuz.database.config import get_db_path

# Set up logger for debug statements
logger = logging.getLogger(__name__)


class WordLookup:
    """
    Handles database lookups for word scansion information.
    
    This class provides methods to query the SQLite database for word codes,
    taqti, and other scansion-related information. It mirrors the C# findWord()
    logic for consistency.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize WordLookup with optional database path.
        
        Args:
            db_path: Optional path to SQLite database. If not provided,
                    uses default path from config.get_db_path()
        """
        if db_path is None:
            self.db_path = get_db_path()
        else:
            self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a SQLite database connection.
        
        Returns:
            sqlite3.Connection: Database connection object
        """
        return sqlite3.connect(self.db_path)
    
    def find_word(self, word: Words) -> Words:
        """
        Find word in database using multiple lookup strategies.
        
        This method mirrors the C# findWord() logic exactly (lines 1663-1838):
        1. First checks exceptions table
        2. Then checks mastertable (with variations " 1" through " 12")
        3. Then checks Plurals table (capitalized, matching C#)
        4. Finally checks Variations table (capitalized, matching C#)
        
        Args:
            word: Words object to look up in database
            
        Returns:
            Words object with populated id, code, taqti, muarrab, language,
            and is_varied lists if found in database. Returns original word
            object if not found.
        """
        logger.debug(f"[DEBUG] find_word() called with word: '{word.word}'")
        # Import here to avoid circular dependency with aruuz.scansion
        from aruuz.scansion import compute_scansion
        
        # Remove araab from search word (matching C#: Araab.removeAraab(wrd.word))
        search_word = remove_araab(word.word)
        logger.debug(f"[DEBUG] find_word() search_word after removing araab: '{search_word}'")
        
        # Strategy 1: Check exceptions table first
        # C#: Opens connection, queries exceptions table
        logger.debug(f"[DEBUG] find_word() Strategy 1: Checking exceptions table")
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # C#: "select * from exceptions where word like @search;"
        # Note: C# uses lowercase 'word' in WHERE clause
        query1 = "SELECT * FROM exceptions WHERE word LIKE ?"
        params1 = (search_word,)
        logger.debug(f"[DEBUG] find_word() executing query 1 (exceptions): '{query1}' with params: {params1}")
        cursor.execute(query1, params1)
        rows = cursor.fetchall()
        logger.debug(f"[DEBUG] find_word() query 1 returned {len(rows)} row(s)")
        
        if rows:
            logger.debug(f"[DEBUG] find_word() found word '{search_word}' in exceptions table")
            # Found in exceptions table - populate and return early
            # C#: while (dataReader.Read()) - process each row
            for row_idx, row in enumerate(rows):
                # Exceptions table structure: id, Word, Taqti, Taqti2, Taqti3
                logger.debug(f"[DEBUG] find_word() exceptions table row {row_idx+1}: id={row[0]}, Word='{row[1] if len(row) > 1 else 'N/A'}', Taqti='{row[2] if len(row) > 2 else 'N/A'}', Taqti2='{row[3] if len(row) > 3 else 'N/A'}', Taqti3='{row[4] if len(row) > 4 else 'N/A'}'")
                # C#: wrd.id.Add(dataReader.GetInt32(0)*-1)
                word.id.append(row[0] * -1)
                
                # C#: wrd.code.Add(dataReader.GetString(2).Replace(" ", ""))
                # Always add taqti1 (C# assumes it's never NULL)
                taqti1 = row[2].replace(" ", "") if row[2] else ""
                word.code.append(taqti1)
                logger.debug(f"[DEBUG] find_word() exceptions table - found taqti1: '{row[2]}' (cleaned: '{taqti1}'), code: '{taqti1}'")
                
                # Handle Taqti2 (may be NULL)
                # C#: try { taqti2 = dataReader.GetString(3).Replace(" ", ""); } catch {}
                # C#: if (!String.IsNullOrEmpty(taqti2)) wrd.code.Add(taqti2);
                try:
                    taqti2 = row[3].replace(" ", "") if row[3] else ""
                    if taqti2:  # Only add if not empty (matching C# String.IsNullOrEmpty check)
                        word.code.append(taqti2)
                        logger.debug(f"[DEBUG] find_word() exceptions table - found taqti2: '{row[3]}' (cleaned: '{taqti2}'), code: '{taqti2}'")
                except (IndexError, TypeError):
                    pass
                
                # Handle Taqti3 (may be NULL)
                # C#: try { taqti3 = dataReader.GetString(4).Replace(" ", ""); } catch {}
                # C#: if (!String.IsNullOrEmpty(taqti3)) wrd.code.Add(taqti3);
                try:
                    taqti3 = row[4].replace(" ", "") if row[4] else ""
                    if taqti3:  # Only add if not empty (matching C# String.IsNullOrEmpty check)
                        word.code.append(taqti3)
                        logger.debug(f"[DEBUG] find_word() exceptions table - found taqti3: '{row[4]}' (cleaned: '{taqti3}'), code: '{taqti3}'")
                except (IndexError, TypeError):
                    pass
            
            # C#: myConn.Close();
            conn.close()
            return word
        else:
            # C#: myConn.Close(); then opens new connection
            conn.close()
            logger.debug(f"[DEBUG] find_word() Strategy 1: No match in exceptions table, trying Strategy 2")
            
            # Strategy 2: Check mastertable with variations
            logger.debug(f"[DEBUG] find_word() Strategy 2: Checking mastertable with variations")
            conn2 = self._get_connection()
            cursor2 = conn2.cursor()
            
            # C#: "select * from mastertable where word like @s or word like @s1 or ... or word like @s12;"
            # Build query with 13 variations: base + " 1" through " 12"
            placeholders = " OR ".join(["word LIKE ?"] * 13)
            query2 = f"SELECT * FROM mastertable WHERE {placeholders}"
            
            # Prepare parameters: search_word, search_word + " 1", ..., search_word + " 12"
            # C#: Parameters are @s, @s1, @s2, ..., @s12 with values: searchWord, searchWord + " 1", etc.
            params2 = [search_word] + [f"{search_word} {i}" for i in range(1, 13)]
            
            logger.debug(f"[DEBUG] find_word() executing query 2 (mastertable): '{query2}'")
            logger.debug(f"[DEBUG] find_word() query 2 params: {params2}")
            cursor2.execute(query2, params2)
            rows = cursor2.fetchall()
            logger.debug(f"[DEBUG] find_word() query 2 returned {len(rows)} row(s)")
            
            if rows:
                logger.debug(f"[DEBUG] find_word() found word '{search_word}' in mastertable")
                # Found in mastertable
                # C#: while (dataReader2.Read()) - process each row
                for row_idx, row in enumerate(rows):
                    # Mastertable structure: ID, Word, Muarrab, Taqti, Language, isVaried, isPlural
                    logger.debug(f"[DEBUG] find_word() mastertable row {row_idx+1}: ID={row[0]}, Word='{row[1] if len(row) > 1 else 'N/A'}', Muarrab='{row[2] if len(row) > 2 else 'N/A'}', Taqti='{row[3] if len(row) > 3 else 'N/A'}', Language='{row[4] if len(row) > 4 else 'N/A'}', isVaried={row[5] if len(row) > 5 else 'N/A'}, isPlural={row[6] if len(row) > 6 else 'N/A'}")
                    # C#: wrd.id.Add(dataReader2.GetInt32(0))
                    word.id.append(row[0])
                    
                    # C#: wrd.muarrab.Add(dataReader2.GetString(2).Trim())
                    muarrab = row[2].strip() if row[2] else ""
                    word.muarrab.append(muarrab)
                    
                    # C#: wrd.taqti.Add(dataReader2.GetString(3).Trim())
                    taqti = row[3].strip() if row[3] else ""
                    word.taqti.append(taqti)
                    logger.debug(f"[DEBUG] find_word() mastertable - found taqti: '{taqti}' for word '{search_word}'")
                    
                    # C#: try { wrd.language.Add(dataReader2.GetString(4)); } catch {}
                    try:
                        language = row[4] if row[4] else ""
                        word.language.append(language)
                    except (IndexError, TypeError):
                        word.language.append("")
                    
                    # C#: wrd.isVaried.Add(dataReader2.GetBoolean(5))
                    # SQLite stores booleans as integers (0/1) - need to convert properly
                    try:
                        # Handle both integer (0/1) and boolean types in SQLite
                        if isinstance(row[5], bool):
                            is_varied = row[5]
                        elif isinstance(row[5], int):
                            is_varied = bool(row[5])
                        else:
                            is_varied = False
                        word.is_varied.append(is_varied)
                    except (IndexError, TypeError):
                        word.is_varied.append(False)
                    
                    # C#: wrd.code.Add(assignCode(wrd))
                    # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                    logger.debug(f"[DEBUG] find_word() calling assign_code() for word '{word.word}' with taqti '{taqti}'")
                    code = compute_scansion(word)
                    word.code.append(code)
                    logger.debug(f"[DEBUG] find_word() assign_code() returned code '{code}' for word '{word.word}'")
                
                # C#: myConn2.Close();
                conn2.close()
                
                # Check if isVaried[0] is True, then query variations table
                # C#: if (wrd.isVaried.Count > 0) { if (wrd.isVaried[0]) { ... } }
                if len(word.is_varied) > 0 and word.is_varied[0]:
                    logger.debug(f"[DEBUG] find_word() Word is_varied=True, checking variations table by id")
                    # C#: Opens new connection and queries variations table by id
                    conn3 = self._get_connection()
                    cursor3 = conn3.cursor()
                    
                    # C#: "select * from variations where id = @id;"
                    # Note: C# uses lowercase 'variations' for this query
                    query3 = "SELECT * FROM variations WHERE id = ?"
                    params3 = (word.id[0],)
                    logger.debug(f"[DEBUG] find_word() executing query 3 (variations by id): '{query3}' with params: {params3}")
                    cursor3.execute(query3, params3)
                    variation_rows = cursor3.fetchall()
                    logger.debug(f"[DEBUG] find_word() query 3 returned {len(variation_rows)} row(s)")
                    
                    if variation_rows:
                        # C#: while (dR2.Read()) - process each variation row
                        for row_idx, row in enumerate(variation_rows):
                            # Variations table structure similar to mastertable: ID, Word, Muarrab, Taqti, ...
                            logger.debug(f"[DEBUG] find_word() variations table (by id) row {row_idx+1}: ID={row[0]}, Word='{row[1] if len(row) > 1 else 'N/A'}', Muarrab='{row[2] if len(row) > 2 else 'N/A'}', Taqti='{row[3] if len(row) > 3 else 'N/A'}', Language='{row[4] if len(row) > 4 else 'N/A'}', isVaried={row[5] if len(row) > 5 else 'N/A'}")
                            # C#: wrd.id.Add(dR2.GetInt32(0))
                            word.id.append(row[0])
                            
                            # C#: wrd.muarrab.Add(dR2.GetString(2).Trim())
                            muarrab = row[2].strip() if row[2] else ""
                            word.muarrab.append(muarrab)
                            
                            # C#: wrd.taqti.Add(dR2.GetString(3).Trim())
                            taqti = row[3].strip() if row[3] else ""
                            word.taqti.append(taqti)
                            logger.debug(f"[DEBUG] find_word() variations table (by id) - found taqti: '{taqti}' for word '{search_word}'")
                            
                            # C#: wrd.code.Add(assignCode(wrd))
                            # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                            logger.debug(f"[DEBUG] find_word() calling assign_code() for word '{word.word}' with taqti '{taqti}'")
                            code = compute_scansion(word)
                            word.code.append(code)
                            logger.debug(f"[DEBUG] find_word() assign_code() returned code '{code}' for word '{word.word}'")
                    
                    # C#: con.Close(); (called twice in C# - once in if, once after)
                    conn3.close()
                
                return word
            else:
                # C#: else //else search in plurals table
                # C#: myConn2.Close();
                conn2.close()
                logger.debug(f"[DEBUG] find_word() Strategy 2: No match in mastertable, trying Strategy 3")
                
                # Strategy 3: Check Plurals table (if mastertable not found)
                logger.debug(f"[DEBUG] find_word() Strategy 3: Checking Plurals table")
                # C#: Opens new connection
                conn3 = self._get_connection()
                cursor3 = conn3.cursor()
                
                # C#: "select * from Plurals where word like @s;"
                # Note: C# uses capitalized 'Plurals' and lowercase 'word' in WHERE clause
                query4 = "SELECT * FROM Plurals WHERE word LIKE ?"
                params4 = (search_word,)
                logger.debug(f"[DEBUG] find_word() executing query 4 (Plurals): '{query4}' with params: {params4}")
                cursor3.execute(query4, params4)
                rows = cursor3.fetchall()
                logger.debug(f"[DEBUG] find_word() query 4 returned {len(rows)} row(s)")
                
                if rows:
                    logger.debug(f"[DEBUG] find_word() found word '{search_word}' in Plurals table")
                    # Found in plurals table
                    # C#: while (dataReader3.Read()) - process each row
                    for row_idx, row in enumerate(rows):
                        # Plurals table structure: ID, Word, Muarrab, Taqti, ...
                        logger.debug(f"[DEBUG] find_word() Plurals table row {row_idx+1}: ID={row[0]}, Word='{row[1] if len(row) > 1 else 'N/A'}', Muarrab='{row[2] if len(row) > 2 else 'N/A'}', Taqti='{row[3] if len(row) > 3 else 'N/A'}', Language='{row[4] if len(row) > 4 else 'N/A'}'")
                        # C#: wrd.id.Add(dataReader3.GetInt32(0))
                        word.id.append(row[0])
                        
                        # C#: wrd.muarrab.Add(dataReader3.GetString(2).Trim())
                        muarrab = row[2].strip() if row[2] else ""
                        word.muarrab.append(muarrab)
                        
                        # C#: wrd.taqti.Add(dataReader3.GetString(3).Trim())
                        taqti = row[3].strip() if row[3] else ""
                        word.taqti.append(taqti)
                        logger.debug(f"[DEBUG] find_word() Plurals table - found taqti: '{taqti}' for word '{search_word}'")
                        
                        # C#: wrd.code.Add(assignCode(wrd))
                        # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                        logger.debug(f"[DEBUG] find_word() calling assign_code() for word '{word.word}' with taqti '{taqti}'")
                        code = compute_scansion(word)
                        word.code.append(code)
                        logger.debug(f"[DEBUG] find_word() assign_code() returned code '{code}' for word '{word.word}'")
                    
                    # C#: myConn3.Close();
                    conn3.close()
                    return word
                else:
                    # C#: else // not found in plurals either? find in variations table
                    # C#: myConn3.Close();
                    conn3.close()
                    logger.debug(f"[DEBUG] find_word() Strategy 3: No match in Plurals table, trying Strategy 4")
                    
                    # Strategy 4: Check Variations table (if plurals not found)
                    logger.debug(f"[DEBUG] find_word() Strategy 4: Checking Variations table")
                    # C#: Opens new connection
                    conn4 = self._get_connection()
                    cursor4 = conn4.cursor()
                    
                    # C#: "select * from Variations where word like @s;"
                    # Note: C# uses capitalized 'Variations' and lowercase 'word' in WHERE clause
                    query5 = "SELECT * FROM Variations WHERE word LIKE ?"
                    params5 = (search_word,)
                    logger.debug(f"[DEBUG] find_word() executing query 5 (Variations): '{query5}' with params: {params5}")
                    cursor4.execute(query5, params5)
                    rows = cursor4.fetchall()
                    logger.debug(f"[DEBUG] find_word() query 5 returned {len(rows)} row(s)")
                    
                    if rows:
                        logger.debug(f"[DEBUG] find_word() found word '{search_word}' in Variations table")
                        # Found in variations table
                        # C#: while (dataReader4.Read()) - process each row
                        for row_idx, row in enumerate(rows):
                            # Variations table structure: ID, Word, Muarrab, Taqti, ...
                            logger.debug(f"[DEBUG] find_word() Variations table row {row_idx+1}: ID={row[0]}, Word='{row[1] if len(row) > 1 else 'N/A'}', Muarrab='{row[2] if len(row) > 2 else 'N/A'}', Taqti='{row[3] if len(row) > 3 else 'N/A'}', Language='{row[4] if len(row) > 4 else 'N/A'}'")
                            # C#: wrd.id.Add(dataReader4.GetInt32(0))
                            word.id.append(row[0])
                            
                            # C#: wrd.muarrab.Add(dataReader4.GetString(2).Trim())
                            muarrab = row[2].strip() if row[2] else ""
                            word.muarrab.append(muarrab)
                            
                            # C#: wrd.taqti.Add(dataReader4.GetString(3).Trim())
                            taqti = row[3].strip() if row[3] else ""
                            word.taqti.append(taqti)
                            logger.debug(f"[DEBUG] find_word() Variations table - found taqti: '{taqti}' for word '{search_word}'")
                            
                            # C#: wrd.code.Add(assignCode(wrd))
                            # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                            logger.debug(f"[DEBUG] find_word() calling assign_code() for word '{word.word}' with taqti '{taqti}'")
                            code = compute_scansion(word)
                            word.code.append(code)
                            logger.debug(f"[DEBUG] find_word() assign_code() returned code '{code}' for word '{word.word}'")
                    
                    # C#: myConn4.Close();
                    conn4.close()
        
        # C#: myConn.Close(); (final close at end of function)
        # Note: This is a safety close - in C# it's called at the very end
        # In our implementation, we've already closed all connections, but this matches the structure
        if len(word.id) == 0:
            logger.debug(f"[DEBUG] find_word() did not find word '{search_word}' in any table")
        else:
            # Summary of all fields populated from database
            logger.debug(f"[DEBUG] find_word() SUMMARY for '{search_word}':")
            logger.debug(f"  - id: {word.id}")
            logger.debug(f"  - code: {word.code}")
            logger.debug(f"  - taqti: {word.taqti}")
            logger.debug(f"  - muarrab: {word.muarrab}")
            logger.debug(f"  - language: {word.language}")
            logger.debug(f"  - is_varied: {word.is_varied}")
        return word

