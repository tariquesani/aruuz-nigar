"""
Database configuration module for Aruuz.

Provides database path resolution with environment variable override support.
"""

import os
from pathlib import Path


# Database filename
DB_FILENAME = 'aruuz_nigar.db'

# Environment variable name for database path override
DB_PATH_ENV_VAR = 'ARUUZ_DB_PATH'


def get_db_path() -> str:
    """
    Get the database path, checking environment variable first, then default.
    
    Checks ARUUZ_DB_PATH environment variable first. If not set, falls back
    to the default path: aruuz_nigar.db in the same directory as this config file
    (python/aruuz/database/aruuz_nigar.db).
    
    The function validates that the file exists and returns an absolute path.
    
    Returns:
        str: Absolute path to the database file
        
    Raises:
        FileNotFoundError: If the database file does not exist at the resolved path
    """
    # Check environment variable first
    env_path = os.getenv(DB_PATH_ENV_VAR)
    if env_path:
        db_path = os.path.abspath(env_path)
    else:
        # Fall back to default path: database file in the same directory as config.py
        # This module is at: python/aruuz/database/config.py
        # Database is at: python/aruuz/database/aruuz_nigar.db
        # Use __file__ to get the directory where this config.py file is located
        current_file = Path(__file__).resolve()
        config_dir = current_file.parent
        db_path = str(config_dir / DB_FILENAME)
    
    # Validate file exists
    if not os.path.exists(db_path):
        # Provide helpful error message with what we tried
        config_file_loc = Path(__file__).resolve()
        config_dir_loc = config_file_loc.parent
        raise FileNotFoundError(
            f"Database file not found at: {db_path}\n"
            f"Config file location: {config_file_loc}\n"
            f"Config directory: {config_dir_loc}\n"
            f"Set {DB_PATH_ENV_VAR} environment variable to override the default path."
        )
    
    return db_path

