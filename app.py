#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for Urdu poetry scansion and meter matching.

This app provides a web interface to scan complete lines of Urdu poetry
and identify matching meters (bahr).
"""

import logging
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


def _get_meter_pattern(so, feet_list_dict):
    """Extract meter pattern from scanOutput."""
    if so.meter_name != 'No meter match found' and so.id is not None:
        try:
            if 0 <= so.id < NUM_METERS:
                return METERS[so.id].replace("/", "")
            elif so.id < NUM_METERS + NUM_VARIED_METERS:
                return METERS_VARIED[so.id - NUM_METERS].replace("/", "")
            elif so.id < NUM_METERS + NUM_VARIED_METERS + NUM_RUBAI_METERS:
                return RUBAI_METERS[so.id - NUM_METERS - NUM_VARIED_METERS].replace("/", "")
            elif so.id <= -2 and feet_list_dict:
                return ''.join(foot['code'] for foot in feet_list_dict)
        except (IndexError, TypeError):
            pass
    return ''.join(foot['code'] for foot in feet_list_dict) if feet_list_dict else None


def _build_word_codes(so):
    """Build word codes list from scanOutput."""
    return [
        {'word': word.word, 'code': so.word_taqti[i] if i < len(so.word_taqti) else ""}
        for i, word in enumerate(so.words)
    ]


def _build_feet_list_dict(so):
    """Build feet list dict from scanOutput."""
    return [{'foot': foot_obj.foot, 'code': foot_obj.code} for foot_obj in so.feet_list]


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route: display form and process multiple lines of poetry."""
    line_results = None
    error = None
    text_input = ""
    poem_dominant_bahrs = []
    
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
                    logging.debug("[DEBUG] Flask app: Using Scansion() with integrated database functionality")
                    scanner = Scansion()
                    
                    # Add all lines
                    line_objects = [Lines(line_text) for line_text in lines]
                    for line_obj in line_objects:
                        scanner.add_line(line_obj)

                    # Step 1: Get dominant bahr per line (scan_line + crunch for each line)
                    per_line_dominants = []
                    for idx, line_obj in enumerate(line_objects):
                        candidates = scanner.match_line_to_meters(line_obj, idx)
                        per_line_dominants.append(scanner.resolve_dominant_meter(candidates) if candidates else [])
                    
                    # Step 2: Get overall dominant bahr for entire poem (scan_lines across all lines)
                    poem_scan_results = scanner.scan_lines()
                    poem_dominant_bahrs = list({
                        so.meter_name for so in poem_scan_results
                        if so.is_dominant and so.meter_name and so.meter_name != 'No meter match found'
                    })
                    
                    # Step 3: Build line_results structure for template
                    line_results = []
                    for idx, (line_obj, dominant_results) in enumerate(zip(line_objects, per_line_dominants)):
                        line_result = {
                            'line_index': idx,
                            'original_line': line_obj.original_line,
                            'results': []
                        }
                        
                        if dominant_results:
                            so = dominant_results[0]  # resolve_dominant_meter() returns list, usually 1 item
                            feet_list_dict = _build_feet_list_dict(so)
                            meter_pattern = _get_meter_pattern(so, feet_list_dict)
                            
                            line_result['results'].append({
                                'meter_name': so.meter_name,
                                'feet': so.feet,
                                'feet_list': feet_list_dict,
                                'word_codes': _build_word_codes(so),
                                'full_code': ''.join(so.word_taqti),
                                'original_line': so.original_line,
                                'is_dominant': True,
                                'meter_pattern': meter_pattern
                            })
                        else:
                            # No match: get word codes
                            word_codes = [
                                {'word': (w := scanner.assign_scansion_to_word(word)).word, 'code': w.code[0] if w.code else "-"}
                                for word in line_obj.words_list
                            ]
                            line_result['results'].append({
                                'meter_name': 'No meter match found',
                                'feet': '',
                                'word_codes': word_codes,
                                'full_code': ''.join(wc['code'] for wc in word_codes),
                                'original_line': line_obj.original_line,
                                'feet_list': []
                            })
                        
                        line_results.append(line_result)
                    
            except Exception as e:
                error = f"Error processing lines: {str(e)}"
                poem_dominant_bahrs = []  # Set empty if error occurred
    
    return render_template('index.html', line_results=line_results, error=error, text_input=text_input, poem_dominant_bahrs=poem_dominant_bahrs)

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
                                word = scanner.assign_scansion_to_word(word)
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

                    scanner.assign_scansion_to_word(word)

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

