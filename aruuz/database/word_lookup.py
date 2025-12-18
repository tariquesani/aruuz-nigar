"""
Database word lookup module for Aruuz.

Provides WordLookup class for querying SQLite database to find word scansion information.
"""

import sqlite3
from typing import Optional
from aruuz.models import Words
from aruuz.utils.araab import remove_araab
from aruuz.scansion import assign_code
from aruuz.database.config import get_db_path


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
        
        This method mirrors the C# findWord() logic:
        1. First checks exceptions table
        2. Then checks mastertable (with variations " 1" through " 12")
        3. Then checks plurals table
        4. Finally checks variations table
        
        Args:
            word: Words object to look up in database
            
        Returns:
            Words object with populated id, code, taqti, muarrab, language,
            and is_varied lists if found in database. Returns original word
            object if not found.
        """
        # Remove araab from search word (matching C# logic)
        search_word = remove_araab(word.word)
        
        # Strategy 1: Check exceptions table first
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Query exceptions table (matching C#: "select * from exceptions where word like @search;")
            cursor.execute("SELECT * FROM exceptions WHERE word LIKE ?", (search_word,))
            rows = cursor.fetchall()
            
            if rows:
                # Found in exceptions table - populate and return early
                # C# logic: always add taqti1, conditionally add taqti2 and taqti3 if not empty
                for row in rows:
                    # Exceptions table structure: id, word, Taqti, Taqti2, Taqti3
                    # C#: wrd.id.Add(dataReader.GetInt32(0)*-1)
                    word.id.append(row[0] * -1)
                    
                    # C#: wrd.code.Add(dataReader.GetString(2).Replace(" ", ""))
                    # Always add taqti1 (C# assumes it's never NULL)
                    taqti1 = row[2].replace(" ", "") if row[2] else ""
                    word.code.append(taqti1)
                    
                    # Handle Taqti2 and Taqti3 (may be NULL)
                    # C#: if (!String.IsNullOrEmpty(taqti2)) wrd.code.Add(taqti2);
                    try:
                        taqti2 = row[3].replace(" ", "") if row[3] else ""
                        if taqti2:  # Only add if not empty (matching C# String.IsNullOrEmpty check)
                            word.code.append(taqti2)
                    except (IndexError, TypeError):
                        pass
                    
                    # C#: if (!String.IsNullOrEmpty(taqti3)) wrd.code.Add(taqti3);
                    try:
                        taqti3 = row[4].replace(" ", "") if row[4] else ""
                        if taqti3:  # Only add if not empty (matching C# String.IsNullOrEmpty check)
                            word.code.append(taqti3)
                    except (IndexError, TypeError):
                        pass
                
                conn.close()
                return word
            
            # Strategy 2: Check mastertable with variations
            # Build query with 13 variations: base + " 1" through " 12"
            # C#: "select * from mastertable where word like @s or word like @s1 or ... or word like @s12;"
            placeholders = " OR ".join(["word LIKE ?"] * 13)
            query = f"SELECT * FROM mastertable WHERE {placeholders}"
            
            # Prepare parameters: search_word, search_word + " 1", ..., search_word + " 12"
            # C#: Parameters are @s, @s1, @s2, ..., @s12 with values: searchWord, searchWord + " 1", etc.
            params = [search_word] + [f"{search_word} {i}" for i in range(1, 13)]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            if rows:
                # Found in mastertable
                # C#: while (dataReader2.Read()) - process each row
                for row in rows:
                    # Mastertable structure: ID, Word, Muarrab, Taqti, Language, isVaried, isPlural
                    # C#: wrd.id.Add(dataReader2.GetInt32(0))
                    word.id.append(row[0])
                    
                    # C#: wrd.muarrab.Add(dataReader2.GetString(2).Trim())
                    muarrab = row[2].strip() if row[2] else ""
                    word.muarrab.append(muarrab)
                    
                    # C#: wrd.taqti.Add(dataReader2.GetString(3).Trim())
                    taqti = row[3].strip() if row[3] else ""
                    word.taqti.append(taqti)
                    
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
                    code = assign_code(word)
                    word.code.append(code)
                
                conn.close()
                
                # Check if isVaried[0] is True, then query variations table
                # C#: if (wrd.isVaried.Count > 0) { if (wrd.isVaried[0]) { ... } }
                if len(word.is_varied) > 0 and word.is_varied[0]:
                    # C#: Opens new connection and queries variations table by id
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        # Query variations table by id (C#: "select * from variations where id = @id;")
                        cursor.execute("SELECT * FROM variations WHERE id = ?", (word.id[0],))
                        variation_rows = cursor.fetchall()
                        
                        if variation_rows:
                            # C#: while (dR2.Read()) - process each variation row
                            for row in variation_rows:
                                # Variations table structure similar to mastertable: ID, Word, Muarrab, Taqti, ...
                                # C#: wrd.id.Add(dR2.GetInt32(0))
                                word.id.append(row[0])
                                
                                # C#: wrd.muarrab.Add(dR2.GetString(2).Trim())
                                muarrab = row[2].strip() if row[2] else ""
                                word.muarrab.append(muarrab)
                                
                                # C#: wrd.taqti.Add(dR2.GetString(3).Trim())
                                taqti = row[3].strip() if row[3] else ""
                                word.taqti.append(taqti)
                                
                                # C#: wrd.code.Add(assignCode(wrd))
                                # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                                code = assign_code(word)
                                word.code.append(code)
                    finally:
                        conn.close()
                
                return word
            
            # Strategy 3: Check plurals table (if mastertable not found)
            # C#: else //else search in plurals table
            # C#: "select * from Plurals where word like @s;"
            cursor.execute("SELECT * FROM plurals WHERE Word LIKE ?", (search_word,))
            rows = cursor.fetchall()
            
            if rows:
                # Found in plurals table
                # C#: while (dataReader3.Read()) - process each row
                for row in rows:
                    # Plurals table structure: ID, Word, Muarrab, Taqti, ...
                    # C#: wrd.id.Add(dataReader3.GetInt32(0))
                    word.id.append(row[0])
                    
                    # C#: wrd.muarrab.Add(dataReader3.GetString(2).Trim())
                    muarrab = row[2].strip() if row[2] else ""
                    word.muarrab.append(muarrab)
                    
                    # C#: wrd.taqti.Add(dataReader3.GetString(3).Trim())
                    taqti = row[3].strip() if row[3] else ""
                    word.taqti.append(taqti)
                    
                    # C#: wrd.code.Add(assignCode(wrd))
                    # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                    code = assign_code(word)
                    word.code.append(code)
                
                conn.close()
                return word
            
            # Strategy 4: Check variations table (if plurals not found)
            # C#: else // not found in plurals either? find in variations table
            # C#: "select * from Variations where word like @s;"
            cursor.execute("SELECT * FROM variations WHERE Word LIKE ?", (search_word,))
            rows = cursor.fetchall()
            
            if rows:
                # Found in variations table
                # C#: while (dataReader4.Read()) - process each row
                for row in rows:
                    # Variations table structure: ID, Word, Muarrab, Taqti, ...
                    # C#: wrd.id.Add(dataReader4.GetInt32(0))
                    word.id.append(row[0])
                    
                    # C#: wrd.muarrab.Add(dataReader4.GetString(2).Trim())
                    muarrab = row[2].strip() if row[2] else ""
                    word.muarrab.append(muarrab)
                    
                    # C#: wrd.taqti.Add(dataReader4.GetString(3).Trim())
                    taqti = row[3].strip() if row[3] else ""
                    word.taqti.append(taqti)
                    
                    # C#: wrd.code.Add(assignCode(wrd))
                    # assign_code uses word.taqti[-1] to get the last taqti, which we just added
                    code = assign_code(word)
                    word.code.append(code)
            
            conn.close()
            return word
            
        except Exception as e:
            # On any error, close connection and return word unchanged
            try:
                conn.close()
            except:
                pass
            # Re-raise to let caller handle (resolver will catch and fallback)
            raise

