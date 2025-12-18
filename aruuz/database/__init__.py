"""
Database module for Aruuz word lookup functionality.
"""

from aruuz.database.word_lookup import WordLookup
from aruuz.database.config import get_db_path

__all__ = ["WordLookup", "get_db_path"]

