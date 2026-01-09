#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple CLI tool to scan individual Urdu words and get their scansion codes.

Usage:
    python scan_word.py <word>
    python scan_word.py "word"
    
    # Interactive mode
    python scan_word.py
    
    # Multiple words
    python scan_word.py "word1" "word2" "word3"
"""

import sys
import argparse
import logging
from pathlib import Path

# Fix Windows console encoding for Unicode
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass

# Configure logging to show DEBUG messages from aruuz modules
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Enable DEBUG logging for aruuz modules
logging.getLogger('aruuz').setLevel(logging.DEBUG)
logging.getLogger('aruuz.scansion').setLevel(logging.DEBUG)
logging.getLogger('aruuz.database').setLevel(logging.DEBUG)
logging.getLogger('aruuz.database.word_lookup').setLevel(logging.DEBUG)

# Add parent directory to path to import aruuz
sys.path.insert(0, str(Path(__file__).parent.parent))

from aruuz.scansion import Scansion, compute_scansion
from aruuz.models import Words
from aruuz.utils.araab import remove_araab

# Create logger for this module
logger = logging.getLogger(__name__)


def scan_word(word_text: str) -> str:
    """
    Scan a single Urdu word and return its scansion code.
    
    Args:
        word_text: Urdu word to scan
        
    Returns:
        Scansion code string (e.g., "=-", "x", "=--")
    """
    if not word_text or not word_text.strip():
        logger.debug("[scan_word] Empty word provided, returning empty code")
        return ""
    
    word_text = word_text.strip()
    logger.debug(f"[scan_word] Starting scan for word: '{word_text}'")
    
    # Create Words object
    word = Words()
    word.word = word_text
    word.taqti = []
    
    # Check if word has taqti information
    stripped = remove_araab(word_text)
    logger.debug(f"[scan_word] Word stripped (no diacritics): '{stripped}', length: {len(stripped)}")
    
    # Use Scansion class to assign code
    scansion = Scansion()
    
    # Check if database is available
    if scansion.word_lookup is not None:
        logger.debug(f"[scan_word] Database lookup available, attempting database search for '{word_text}'")
    else:
        logger.debug(f"[scan_word] Database lookup not available, will use heuristics only")
    
    # Store original state to detect if database was used
    original_code_count = len(word.code)
    
    word = scansion.assign_scansion_to_word(word)
    
    # Determine which strategy was used
    if len(word.id) > 0:
        logger.debug(f"[scan_word] Word found in database. ID(s): {word.id}, Code(s): {word.code}, Taqti: {word.taqti}")
        logger.debug(f"[scan_word] Database lookup successful for '{word_text}'")
    elif original_code_count == 0 and len(word.code) > 0:
        logger.debug(f"[scan_word] Word not found in database, used heuristics. Code: {word.code}")
        if word.modified:
            logger.debug(f"[scan_word] Word was modified (e.g., compound word split)")
    
    # Return the code
    if word.code and len(word.code) > 0:
        final_code = word.code[0]
        logger.debug(f"[scan_word] Final code for '{word_text}': '{final_code}'")
        if len(word.code) > 1:
            logger.debug(f"[scan_word] Multiple code variations available: {word.code}")
        return final_code
    
    logger.debug(f"[scan_word] No code generated for '{word_text}'")
    return ""


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Scan Urdu words and get their scansion codes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "word"                    # Scan single word
  %(prog)s "word1" "word2"           # Scan multiple words
  %(prog)s                           # Interactive mode
  %(prog)s -v "word"                 # Verbose output
  %(prog)s -i                        # Interactive mode
        """
    )
    
    parser.add_argument(
        'words',
        nargs='*',
        help='Urdu word(s) to scan'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show verbose output with word details'
    )
    
    parser.add_argument(
        '-i', '--interactive',
        action='store_true',
        help='Run in interactive mode (enter words one by one)'
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='Read words from file (one word per line)'
    )
    
    args = parser.parse_args()
    
    # Interactive mode
    if args.interactive or (not args.words and sys.stdin.isatty()):
        print("Urdu Word Scansion Tool")
        print("Enter Urdu words to scan (press Ctrl+C or 'quit' to exit)")
        print("-" * 50)
        
        # Fix input encoding for Windows
        if sys.platform == 'win32':
            try:
                import msvcrt
                import codecs
                sys.stdin = codecs.getreader('utf-8')(sys.stdin.buffer, errors='replace')
            except (ImportError, AttributeError):
                pass
        
        try:
            while True:
                word_input = input("\nWord: ").strip()
                
                if not word_input or word_input.lower() in ['quit', 'exit', 'q']:
                    print("Exiting...")
                    break
                
                logger.debug(f"[main] Processing word in interactive mode: '{word_input}'")
                code = scan_word(word_input)
                if code:
                    print(f"Code: {code}")
                    if args.verbose:
                        print(f"  Word: {word_input}")
                        print(f"  Length: {len(word_input)} characters")
                else:
                    print("No code generated")
                    logger.warning(f"[main] No code generated for word: '{word_input}'")
        
        except KeyboardInterrupt:
            print("\nExiting...")
        return
    
    # File input mode
    if args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                file_words = [line.strip() for line in f if line.strip()]
            
            if not file_words:
                print(f"No words found in {args.file}")
                return
            
            print(f"Reading {len(file_words)} word(s) from {args.file}\n")
            logger.debug(f"[main] Processing {len(file_words)} word(s) from file: {args.file}")
            for idx, word_text in enumerate(file_words, 1):
                logger.debug(f"[main] Processing word {idx}/{len(file_words)}: '{word_text}'")
                code = scan_word(word_text)
                
                if args.verbose:
                    print(f"Word: {word_text}")
                    print(f"Code: {code}")
                    print(f"Length: {len(word_text)} characters")
                    print()
                else:
                    print(f"{word_text}: {code}")
            return
        except FileNotFoundError:
            print(f"Error: File '{args.file}' not found")
            return
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    
    # Batch mode - process all provided words
    if not args.words:
        parser.print_help()
        return
    
    # Process each word
    logger.debug(f"[main] Processing {len(args.words)} word(s) in batch mode")
    for idx, word_text in enumerate(args.words, 1):
        logger.debug(f"[main] Processing word {idx}/{len(args.words)}: '{word_text}'")
        code = scan_word(word_text)
        
        if args.verbose:
            print(f"Word: {word_text}")
            print(f"Code: {code}")
            print(f"Length: {len(word_text)} characters")
            print()
        else:
            print(f"{word_text}: {code}")


if __name__ == "__main__":
    main()

