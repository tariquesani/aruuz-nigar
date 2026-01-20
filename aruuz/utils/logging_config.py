"""
Logging Configuration Helper

Provides centralized logging configuration for the application.
Can be imported and called from anywhere to set up logging.
"""

import logging
from pathlib import Path
from typing import Optional

# Global flag to track if console logging should be silenced
_CONSOLE_LOGGING_SILENCED = False

# Global flag to track if file logging should be silenced
_FILE_LOGGING_SILENCED = False


def setup_logging(logs_dir: Optional[Path] = None) -> None:
    """
    Configure logging for the application.
    
    Sets up:
    - DEBUG logger: console and file handler (logs/debug.log)
    - Explain logger: file handler only (logs/explain.log) at INFO level
    
    This function is idempotent - it can be called multiple times safely.
    
    Args:
        logs_dir: Optional directory for log files. If None, uses 'logs' directory
                 relative to the calling module's parent directory.
    """
    # Determine logs directory
    if logs_dir is None:
        # Try to find logs directory relative to common locations
        # Default to 'logs' in current working directory
        logs_dir = Path('logs')
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Log format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Configure root logger (only if not already configured)
    global _CONSOLE_LOGGING_SILENCED, _FILE_LOGGING_SILENCED
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.DEBUG)
        
        # Create file handler for debug.log (only if file logging is not silenced)
        if not _FILE_LOGGING_SILENCED:
            file_handler = logging.FileHandler(logs_dir / 'debug.log', encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            root_logger.addHandler(file_handler)
        
        # Only create console handler if console logging is not silenced
        if not _CONSOLE_LOGGING_SILENCED:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logging.Formatter(log_format, date_format))
            root_logger.addHandler(console_handler)
    
    # Enable DEBUG logging for aruuz modules (unless silenced)
    aruuz_level = logging.WARNING if _CONSOLE_LOGGING_SILENCED else logging.DEBUG
    logging.getLogger('aruuz').setLevel(aruuz_level)
    logging.getLogger('aruuz.scansion').setLevel(aruuz_level)
    logging.getLogger('aruuz.database').setLevel(aruuz_level)
    logging.getLogger('aruuz.database.word_lookup').setLevel(aruuz_level)
    
    # Remove any console handlers if silenced
    if _CONSOLE_LOGGING_SILENCED:
        handlers_to_remove = [
            h for h in root_logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
        ]
        for handler in handlers_to_remove:
            root_logger.removeHandler(handler)
    
    # Remove any file handlers if silenced
    if _FILE_LOGGING_SILENCED:
        handlers_to_remove = [
            h for h in root_logger.handlers
            if isinstance(h, logging.FileHandler)
        ]
        for handler in handlers_to_remove:
            root_logger.removeHandler(handler)
        
        # Also remove file handlers from explain logger
        explain_logger = logging.getLogger('aruuz.explain')
        handlers_to_remove = [
            h for h in explain_logger.handlers
            if isinstance(h, logging.FileHandler)
        ]
        for handler in handlers_to_remove:
            explain_logger.removeHandler(handler)
    
    # Reduce noise from other loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Configure explain logger (separate from DEBUG logger)
    # Explain logs are user-facing semantic events at INFO level
    explain_logger = logging.getLogger('aruuz.explain')
    
    # Only configure if not already configured (check for handlers)
    # Only create file handler if file logging is not silenced
    if not explain_logger.handlers and not _FILE_LOGGING_SILENCED:
        explain_file_handler = logging.FileHandler(logs_dir / 'explain.log', encoding='utf-8')
        explain_file_handler.setLevel(logging.INFO)
        explain_file_handler.setFormatter(logging.Formatter(log_format, date_format))
        explain_logger.setLevel(logging.INFO)
        explain_logger.addHandler(explain_file_handler)
        # Prevent propagation to root logger (explain logs only go to file)
        explain_logger.propagate = False


def silence_console_logging():
    """
    Silence console logging output while keeping file logging.
    
    This is useful for tests or scripts where you don't want DEBUG logs
    cluttering the console output. File logs will still be written.
    
    Sets a flag that setup_logging() will respect, and also removes any
    existing console handlers and sets logger levels to WARNING.
    
    Call this BEFORE importing aruuz modules for best results.
    """
    global _CONSOLE_LOGGING_SILENCED
    _CONSOLE_LOGGING_SILENCED = True
    
    # Remove existing console handlers
    root_logger = logging.getLogger()
    handlers_to_remove = [
        h for h in root_logger.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    ]
    for handler in handlers_to_remove:
        root_logger.removeHandler(handler)
    
    # Set aruuz logger levels to WARNING
    logging.getLogger('aruuz').setLevel(logging.WARNING)
    logging.getLogger('aruuz.scansion').setLevel(logging.WARNING)
    logging.getLogger('aruuz.database').setLevel(logging.WARNING)
    logging.getLogger('aruuz.database.word_lookup').setLevel(logging.WARNING)


def silence_file_logging():
    """
    Silence file logging output while keeping console logging.
    
    This is useful for tests or scripts where you don't want log files
    to be created or written to. Console logs will still be output.
    
    Sets a flag that setup_logging() will respect, and also removes any
    existing file handlers from both the root logger and explain logger.
    
    Call this BEFORE importing aruuz modules for best results.
    """
    global _FILE_LOGGING_SILENCED
    _FILE_LOGGING_SILENCED = True
    
    # Remove existing file handlers from root logger
    root_logger = logging.getLogger()
    handlers_to_remove = [
        h for h in root_logger.handlers
        if isinstance(h, logging.FileHandler)
    ]
    for handler in handlers_to_remove:
        root_logger.removeHandler(handler)
    
    # Remove existing file handlers from explain logger
    explain_logger = logging.getLogger('aruuz.explain')
    handlers_to_remove = [
        h for h in explain_logger.handlers
        if isinstance(h, logging.FileHandler)
    ]
    for handler in handlers_to_remove:
        explain_logger.removeHandler(handler)