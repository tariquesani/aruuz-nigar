"""
Logging Configuration Helper

Provides centralized logging configuration for the application.
Can be imported and called from anywhere to set up logging.
"""

import logging
from pathlib import Path
from typing import Optional


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
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.DEBUG)
        
        # Create file handler for debug.log
        file_handler = logging.FileHandler(logs_dir / 'debug.log', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        root_logger.addHandler(file_handler)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        root_logger.addHandler(console_handler)
    
    # Enable DEBUG logging for aruuz modules
    logging.getLogger('aruuz').setLevel(logging.DEBUG)
    logging.getLogger('aruuz.scansion').setLevel(logging.DEBUG)
    logging.getLogger('aruuz.database').setLevel(logging.DEBUG)
    logging.getLogger('aruuz.database.word_lookup').setLevel(logging.DEBUG)
    
    # Reduce noise from other loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Configure explain logger (separate from DEBUG logger)
    # Explain logs are user-facing semantic events at INFO level
    explain_logger = logging.getLogger('aruuz.explain')
    
    # Only configure if not already configured (check for handlers)
    if not explain_logger.handlers:
        explain_file_handler = logging.FileHandler(logs_dir / 'explain.log', encoding='utf-8')
        explain_file_handler.setLevel(logging.INFO)
        explain_file_handler.setFormatter(logging.Formatter(log_format, date_format))
        explain_logger.setLevel(logging.INFO)
        explain_logger.addHandler(explain_file_handler)
        # Prevent propagation to root logger (explain logs only go to file)
        explain_logger.propagate = False
