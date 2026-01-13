"""
Explain Logging Helper

Provides access to the explain logger for user-facing semantic event logging.
"""

import logging
from pathlib import Path


def get_explain_logger():
    """
    Get the explain logger instance.
    
    The explain logger writes user-facing semantic events to logs/explain.log
    at INFO level. It is separate from the DEBUG logger and focuses on
    explaining "why" the engine made decisions.
    
    If setup_logging() has not been called, this function will automatically
    configure logging with default settings to ensure explain logs work.
    
    Returns:
        Logger instance named 'aruuz.explain'
    """
    logger = logging.getLogger('aruuz.explain')
    
    # Auto-configure if no handlers exist (setup_logging() wasn't called)
    if not logger.handlers:
        # Import here to avoid circular dependency
        from aruuz.utils.logging_config import setup_logging
        setup_logging()
    
    return logger
