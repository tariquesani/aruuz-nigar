#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for Urdu poetry scansion and meter matching.

This app provides a web interface to scan complete lines of Urdu poetry
and identify matching meters (bahr).
"""

import logging
import re
from flask import Flask, render_template, request
from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS, SPECIAL_METERS,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, NUM_SPECIAL_METERS
) 

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

# Reduce noise from other loggers
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['JSON_AS_ASCII'] = False  # Important for Urdu JSON


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route: display form and process multiple lines of poetry."""
    line_results = None
    error = None
    text_input = ""
    
    if request.method == 'POST':
        text_input = request.form.get('text', '').strip()
        
        if not text_input:
            error = "Please enter Urdu poetry lines"
        else:
            try:
                # Split input by newlines (matching C# behavior)
                lines = [line.strip() for line in text_input.split('\n') if line.strip()]
                
                if not lines:
                    error = "Please enter at least one line of Urdu poetry"
                else:
                    # Use Scansion with integrated database functionality (matches C# implementation)
                    # Scansion() will automatically initialize WordLookup for database access if available
                    # word_code() will try: database lookup -> heuristics (fallback)
                    logging.debug("[DEBUG] Flask app: Using Scansion() with integrated database functionality")
                    scanner = Scansion()
                    
                    # Add all lines
                    line_objects = []
                    for line_text in lines:
                        line_obj = Lines(line_text)
                        scanner.add_line(line_obj)
                        line_objects.append(line_obj)

                    # Use scan_lines() to get all results with crunch() applied
                    # This will mark dominant meters with is_dominant flag
                    all_scan_results = scanner.scan_lines()
                    
                    # Group results by line for display
                    # Initialize line_results structure - one entry per line
                    line_results = []
                    for idx, line_obj in enumerate(line_objects):
                        line_results.append({
                            'line_index': idx,
                            'original_line': line_obj.original_line,
                            'results': []
                        })
                    
                    # Group scan results by original_line
                    for so in all_scan_results:
                        # Find which line this result belongs to
                        for idx, line_obj in enumerate(line_objects):
                            if so.original_line == line_obj.original_line:
                                # Build word-by-word display
                                word_codes = []
                                for i, word in enumerate(so.words):
                                    code = so.word_taqti[i] if i < len(so.word_taqti) else ""
                                    word_codes.append({
                                        'word': word.word,
                                        'code': code
                                    })
                                
                                # Extract syllables for the line
                                syllables = []
                                for i, word in enumerate(so.words):
                                    if word.breakup and len(word.breakup) > 0:
                                        # Use breakup if available
                                        syllables.extend(word.breakup)
                                    elif word.taqti and len(word.taqti) > 0:
                                        # Derive from taqti by splitting on '+' or space
                                        taqti_str = word.taqti[0]
                                        taqti_parts = re.split(r'[+\s]+', taqti_str)
                                        syllables.extend([part for part in taqti_parts if part.strip()])
                                    else:
                                        # Fallback: use word code length to estimate syllables
                                        code_str = so.word_taqti[i] if i < len(so.word_taqti) else ""
                                        if code_str:
                                            # Each character in code_str represents a syllable
                                            # Use the word text as a placeholder for each syllable
                                            # This is approximate - actual syllable text would need more complex logic
                                            for _ in range(len(code_str)):
                                                syllables.append(word.word)
                                        else:
                                            # If no code, use whole word as single syllable
                                            syllables.append(word.word)
                                
                                # Ensure syllables list matches full_code length
                                full_code = ''.join(so.word_taqti)
                                full_code_len = len(full_code)
                                if len(syllables) > full_code_len:
                                    # Truncate if too many syllables
                                    syllables = syllables[:full_code_len]
                                elif len(syllables) < full_code_len:
                                    # Pad with word text if too few syllables
                                    last_word = so.words[-1].word if so.words else ""
                                    while len(syllables) < full_code_len:
                                        syllables.append(last_word)
                                
                                # Convert feet_list to list of dicts for template
                                feet_list_dict = []
                                for foot_obj in so.feet_list:
                                    feet_list_dict.append({
                                        'foot': foot_obj.foot,
                                        'code': foot_obj.code
                                    })
                                
                                # Get meter pattern for resolved notation (when there's a match)
                                # This gives us the resolved pattern from the bahr (no x)
                                meter_pattern = None
                                if so.meter_name != 'No meter match found' and so.id is not None:
                                    try:
                                        if so.id >= 0 and so.id < NUM_METERS:
                                            # Regular meter - get pattern from METERS array
                                            meter_pattern = METERS[so.id].replace("/", "")
                                        elif so.id < NUM_METERS + NUM_VARIED_METERS:
                                            # Varied meter
                                            meter_pattern = METERS_VARIED[so.id - NUM_METERS].replace("/", "")
                                        elif so.id < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                                            # Rubai meter
                                            meter_pattern = RUBAI_METERS[so.id - NUM_METERS - NUM_VARIED_METERS].replace("/", "")
                                        elif so.id == -2:
                                            # Rubai meter (special case - id is -2)
                                            # Try to get pattern from feet_list codes
                                            if feet_list_dict:
                                                meter_pattern = ''.join([foot['code'] for foot in feet_list_dict])
                                        elif so.id < -2:
                                            # Special meters (Hindi/Zamzama) - id is negative
                                            # For special meters, the full_code from word_taqti should be resolved
                                            # But if it still has 'x', use feet_list if available
                                            if feet_list_dict:
                                                meter_pattern = ''.join([foot['code'] for foot in feet_list_dict])
                                            # If no feet_list, the word_taqti should already be resolved for special meters
                                    except (IndexError, TypeError):
                                        pass
                                
                                # If meter_pattern still not found, try to reconstruct from feet_list
                                if not meter_pattern and feet_list_dict:
                                    meter_pattern = ''.join([foot['code'] for foot in feet_list_dict])
                                
                                # Final fallback: for special meters without feet_list, 
                                # the word_taqti should be the resolved code (but may still have 'x')
                                # In this case, we'll use it but it might still show 'x'
                                
                                line_results[idx]['results'].append({
                                    'meter_name': so.meter_name,
                                    'feet': so.feet,
                                    'feet_list': feet_list_dict,
                                    'word_codes': word_codes,
                                    'full_code': ''.join(so.word_taqti),
                                    'original_line': so.original_line,
                                    'is_dominant': so.is_dominant,
                                    'syllables': syllables,
                                    'meter_pattern': meter_pattern
                                })
                                break
                    
                    # Handle lines with no matches - add word codes
                    for idx, line_obj in enumerate(line_objects):
                        if len(line_results[idx]['results']) == 0:
                            # Get word codes even if no meter match
                            word_codes = []
                            for word in line_obj.words_list:
                                word = scanner.word_code(word)
                                code = word.code[0] if word.code else "-"
                                word_codes.append({
                                    'word': word.word,
                                    'code': code
                                })

                            # Extract syllables for no-match case
                            syllables = []
                            for word in line_obj.words_list:
                                if word.breakup and len(word.breakup) > 0:
                                    syllables.extend(word.breakup)
                                elif word.taqti and len(word.taqti) > 0:
                                    taqti_str = word.taqti[0]
                                    taqti_parts = re.split(r'[+\s]+', taqti_str)
                                    syllables.extend([part for part in taqti_parts if part.strip()])
                                else:
                                    # Fallback: use word as single syllable
                                    syllables.append(word.word)
                            
                            # Ensure syllables list matches full_code length
                            full_code = ''.join([wc['code'] for wc in word_codes])
                            full_code_len = len(full_code)
                            if len(syllables) > full_code_len:
                                # Truncate if too many syllables
                                syllables = syllables[:full_code_len]
                            elif len(syllables) < full_code_len:
                                # Pad with word text if too few syllables
                                last_word = line_obj.words_list[-1].word if line_obj.words_list else ""
                                while len(syllables) < full_code_len:
                                    syllables.append(last_word)

                            line_results[idx]['results'].append({
                                'meter_name': 'No meter match found',
                                'feet': '',
                                'word_codes': word_codes,
                                'full_code': full_code,
                                'original_line': line_obj.original_line,
                                'syllables': syllables,
                                'feet_list': []
                            })
                    
            except Exception as e:
                error = f"Error processing lines: {str(e)}"

    # Extract dominant bahr(s) from results - crunch() already determined this
    # All results with is_dominant=True are from the dominant meter
    dominant_bahrs = []
    if line_results:
        seen_bahrs = set()
        for line_data in line_results:
            if line_data.get('results'):
                # Find results marked as dominant by crunch()
                for result in line_data['results']:
                    if result.get('is_dominant') and result.get('meter_name') != 'No meter match found':
                        bahr_name = result['meter_name']
                        if bahr_name not in seen_bahrs:
                            dominant_bahrs.append(bahr_name)
                            seen_bahrs.add(bahr_name)
    
    # print(line_results)
    
    return render_template('index.html', line_results=line_results, error=error, text_input=text_input, dominant_bahrs=dominant_bahrs)
@app.route('/islah', methods=['GET', 'POST'])
def islah():
    """Main route: display form and process multiple lines of poetry."""
    line_results = None
    error = None
    text_input = ""
    
    if request.method == 'POST':
        text_input = request.form.get('text', '').strip()
        
        if not text_input:
            error = "Please enter Urdu poetry lines"
        else:
            try:
                # Split input by newlines (matching C# behavior)
                lines = [line.strip() for line in text_input.split('\n') if line.strip()]
                
                if not lines:
                    error = "Please enter at least one line of Urdu poetry"
                else:
                    # Use Scansion with integrated database functionality (matches C# implementation)
                    # Scansion() will automatically initialize WordLookup for database access if available
                    # word_code() will try: database lookup -> heuristics (fallback)
                    logging.debug("[DEBUG] Flask app: Using Scansion() with integrated database functionality")
                    scanner = Scansion()
                    
                    # Add all lines
                    line_objects = []
                    for line_text in lines:
                        line_obj = Lines(line_text)
                        scanner.add_line(line_obj)
                        line_objects.append(line_obj)

                    # Use scan_lines() to get all results with crunch() applied
                    # This will mark dominant meters with is_dominant flag
                    all_scan_results = scanner.scan_lines()
                    
                    # Group results by line for display
                    # Initialize line_results structure - one entry per line
                    line_results = []
                    for idx, line_obj in enumerate(line_objects):
                        line_results.append({
                            'line_index': idx,
                            'original_line': line_obj.original_line,
                            'results': []
                        })
                    
                    # Group scan results by original_line
                    for so in all_scan_results:
                        # Find which line this result belongs to
                        for idx, line_obj in enumerate(line_objects):
                            if so.original_line == line_obj.original_line:
                                # Build word-by-word display
                                word_codes = []
                                for i, word in enumerate(so.words):
                                    code = so.word_taqti[i] if i < len(so.word_taqti) else ""
                                    word_codes.append({
                                        'word': word.word,
                                        'code': code
                                    })
                                
                                # Convert feet_list to list of dicts for template
                                feet_list_dict = []
                                for foot_obj in so.feet_list:
                                    feet_list_dict.append({
                                        'foot': foot_obj.foot,
                                        'code': foot_obj.code
                                    })
                                
                                line_results[idx]['results'].append({
                                    'meter_name': so.meter_name,
                                    'feet': so.feet,
                                    'feet_list': feet_list_dict,
                                    'word_codes': word_codes,
                                    'full_code': ''.join(so.word_taqti),
                                    'original_line': so.original_line,
                                    'is_dominant': so.is_dominant
                                })
                                break
                    
                    # Handle lines with no matches - add word codes
                    for idx, line_obj in enumerate(line_objects):
                        if len(line_results[idx]['results']) == 0:
                            # Get word codes even if no meter match
                            word_codes = []
                            for word in line_obj.words_list:
                                word = scanner.word_code(word)
                                code = word.code[0] if word.code else "-"
                                word_codes.append({
                                    'word': word.word,
                                    'code': code
                                })

                            line_results[idx]['results'].append({
                                'meter_name': 'No meter match found',
                                'feet': '',
                                'word_codes': word_codes,
                                'full_code': ''.join([wc['code'] for wc in word_codes]),
                                'original_line': line_obj.original_line
                            })
                    
            except Exception as e:
                error = f"Error processing lines: {str(e)}"

    # print(line_results)
    
    return render_template('islah.html', line_results=line_results, error=error, text_input=text_input)


@app.route('/debug/word', methods=['GET', 'POST'])
def debug_word():
    """
    Debug route for testing single-word scansion.
    Outputs word → code mapping for manual RTL inspection.
    """
    word_input = ""
    result = None
    error = None

    if request.method == 'POST':
        word_input = request.form.get('word', '').strip()

        if not word_input:
            error = "Please enter a single Urdu word"
        else:
            try:
                scanner = Scansion()

                # Create a dummy Lines object to reuse existing logic
                line_obj = Lines(word_input)

                if not line_obj.words_list:
                    error = "Invalid word after cleaning"
                else:
                    word = line_obj.words_list[0]

                    scanner.word_code(word)

                    result = {
                        'word': word.word,
                        'codes': word.code,
                        'used_database': bool(word.id),
                        'ids': word.id,
                        'taqti': word.taqti,
                        'muarrab': word.muarrab
                    }

                    # Optional logging (very useful)
                    logging.debug(
                        "[WORD TEST] %s → %s (db=%s)",
                        word.word,
                        word.code,
                        bool(word.id)
                    )

            except Exception as e:
                error = f"Error processing word: {str(e)}"

    return render_template(
        'debug_word.html',
        word_input=word_input,
        result=result,
        error=error
    )

@app.route('/debug/fragment', methods=['GET', 'POST'])
def debug_fragment():
    """
    Debug route for testing short multi-word fragments.
    Exercises word-level scansion + contextual adjustments
    (izafat, ataf, al, grafting) but does not care about meter output.
    """
    text_input = ""
    result = None
    error = None

    if request.method == 'POST':
        text_input = request.form.get('text', '').strip()

        if not text_input:
            error = "Please enter a short Urdu fragment (2–3 words)"
        else:
            try:
                scanner = Scansion()

                line_obj = Lines(text_input)
                scanner.add_line(line_obj)

                # Run the real engine path
                # This applies word_code + contextual adjustments
                scanner.scan_lines()

                # Inspect post-contextual word state
                words_debug = []
                combined_codes = []

                for word in line_obj.words_list:
                    words_debug.append({
                        'word': word.word,
                        'codes': word.code,
                        'taqti': word.taqti,
                        'muarrab': word.muarrab,
                        'used_database': bool(word.id),
                    })

                    combined_codes.append(word.code if word.code else [""])

                result = {
                    'original_text': line_obj.original_line,
                    'words': words_debug,
                    'combined_code_options': combined_codes,
                    'note': (
                        "Codes shown are after contextual adjustments "
                        "(izafat/ataf/al/grafting), before meter dominance."
                    )
                }


                logging.debug(
                    "[FRAGMENT TEST] %s → %s",
                    text_input,
                    combined_codes
                )

            except Exception as e:
                error = f"Error processing fragment: {str(e)}"

    return render_template(
        'debug_fragment.html',
        text_input=text_input,
        result=result,
        error=error
    )

@app.route('/debug/tree', methods=['GET', 'POST'])
def debug_tree():
    """
    Debug route for visualizing CodeTree structure.
    Shows tree visualization, all paths, and summary statistics.
    """
    text_input = ""
    result = None
    error = None

    if request.method == 'POST':
        text_input = request.form.get('text', '').strip()

        if not text_input:
            error = "Please enter Urdu poetry line(s)"
        else:
            try:
                scanner = Scansion()
                
                # Process the line
                line_obj = Lines(text_input)
                scanner.add_line(line_obj)
                
                # Build the tree
                from aruuz.tree.code_tree import CodeTree
                tree = CodeTree.build_from_line(
                    line_obj,
                    error_param=scanner.error_param,
                    fuzzy=scanner.fuzzy,
                    free_verse=scanner.free_verse
                )
                
                # Get visualization
                tree_visualization = tree.visualize()
                
                # Get all paths
                all_paths = tree.get_all_paths()
                paths_display = []
                for path in all_paths:
                    # Skip root node in display
                    path_codes = [loc.code for loc in path if loc.code != "root"]
                    path_info = []
                    for loc in path:
                        if loc.code != "root":
                            path_info.append({
                                'code': loc.code,
                                'word_ref': loc.word_ref,
                                'word': loc.word,
                                'code_ref': loc.code_ref
                            })
                    paths_display.append({
                        'full_code': ''.join(path_codes),
                        'locations': path_info
                    })
                
                # Get summary
                summary = tree.get_summary()
                
                result = {
                    'original_text': line_obj.original_line,
                    'tree_visualization': tree_visualization,
                    'total_paths': len(all_paths),
                    'paths': paths_display,
                    'summary': summary
                }
                
                logging.debug(
                    "[TREE DEBUG] %s → %d paths, %d nodes",
                    text_input,
                    len(all_paths),
                    summary['total_nodes']
                )

            except Exception as e:
                error = f"Error processing tree: {str(e)}"
                import traceback
                logging.error(traceback.format_exc())

    return render_template(
        'debug_tree.html',
        text_input=text_input,
        result=result,
        error=error
    )


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

