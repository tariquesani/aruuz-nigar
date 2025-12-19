#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for Urdu poetry scansion and meter matching.

This app provides a web interface to scan complete lines of Urdu poetry
and identify matching meters (bahr).
"""

from flask import Flask, render_template, request
from aruuz.models import Lines
from aruuz.scansion_db import ScansionWithDatabase
from aruuz.scansion import Scansion 

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
                    # Use pure heuristic Scansion for the main index route
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
                                
                                line_results[idx]['results'].append({
                                    'meter_name': so.meter_name,
                                    'feet': so.feet,
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
    
    return render_template('index.html', line_results=line_results, error=error, text_input=text_input)


@app.route('/test', methods=['GET', 'POST'])
def test():
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
                            # Create separate heuristic and database-backed scanners
                            heuristic_scanner = Scansion()
                            db_scanner = ScansionWithDatabase()

                            # Build separate line objects for each scanner so they don't share Words
                            heuristic_line_objects = []
                            db_line_objects = []
                            for line_text in lines:
                                h_line = Lines(line_text)
                                d_line = Lines(line_text)
                                heuristic_scanner.add_line(h_line)
                                db_scanner.add_line(d_line)
                                heuristic_line_objects.append(h_line)
                                db_line_objects.append(d_line)

                            # Initialize line_results structure - one entry per line
                            line_results = []
                            for idx, h_line in enumerate(heuristic_line_objects):
                                line_results.append({
                                    'line_index': idx,
                                    'original_line': h_line.original_line,
                                    # Store heuristic and DB results separately
                                    'heuristic_results': [],
                                    'db_results': []
                                })

                            # Process each line individually to maintain correct order
                            for idx, (h_line, d_line) in enumerate(zip(heuristic_line_objects, db_line_objects)):
                                # --- Heuristic scansion ---
                                # Use scan_lines() to get results with crunch() applied
                                heuristic_all_results = heuristic_scanner.scan_lines()
                                
                                # Filter results for this line
                                for so in heuristic_all_results:
                                    if so.original_line == h_line.original_line:
                                        # Build word-by-word display for heuristics
                                        word_codes = []
                                        for i, word in enumerate(so.words):
                                            code = so.word_taqti[i] if i < len(so.word_taqti) else ""
                                            word_codes.append({
                                                'word': word.word,
                                                'code': code
                                            })

                                        line_results[idx]['heuristic_results'].append({
                                            'meter_name': so.meter_name,
                                            'feet': so.feet,
                                            'word_codes': word_codes,
                                            'full_code': ''.join(so.word_taqti),
                                            'original_line': so.original_line,
                                            'is_dominant': so.is_dominant
                                        })

                                # --- Database-backed scansion (via resolver) ---
                                # Use scan_lines() to get results with crunch() applied
                                db_all_results = db_scanner.scan_lines()
                                
                                # Filter results for this line
                                for so in db_all_results:
                                    if so.original_line == d_line.original_line:
                                        # Build word-by-word display, marking DB-derived codes
                                        word_codes_db = []
                                        for i, word in enumerate(so.words):
                                            code = so.word_taqti[i] if i < len(so.word_taqti) else ""
                                            # Consider a word DB-backed if it has any non-synthetic ID
                                            word_ids = getattr(word, "id", [])
                                            from_db = bool(word_ids) and any(
                                                (id_val is not None and id_val != -1) for id_val in word_ids
                                            )
                                            word_codes_db.append({
                                                'word': word.word,
                                                'code': code,
                                                'from_db': from_db
                                            })

                                        line_results[idx]['db_results'].append({
                                            'meter_name': so.meter_name,
                                            'feet': so.feet,
                                            'word_codes': word_codes_db,
                                            'full_code': ''.join(so.word_taqti),
                                            'original_line': so.original_line,
                                            'is_dominant': so.is_dominant
                                        })

                            # Handle lines with no matches - add word codes for both scanners
                            for idx, (h_line, d_line) in enumerate(zip(heuristic_line_objects, db_line_objects)):
                                # Heuristic fallback when no meter match
                                if len(line_results[idx]['heuristic_results']) == 0:
                                    word_codes = []
                                    for word in h_line.words_list:
                                        word = heuristic_scanner.word_code(word)
                                        code = word.code[0] if word.code else "-"
                                        word_codes.append({
                                            'word': word.word,
                                            'code': code
                                        })

                                    line_results[idx]['heuristic_results'].append({
                                        'meter_name': 'No meter match found',
                                        'feet': '',
                                        'word_codes': word_codes,
                                        'full_code': ''.join([wc['code'] for wc in word_codes]),
                                        'original_line': h_line.original_line
                                    })

                                # Database-backed fallback when no meter match
                                if len(line_results[idx]['db_results']) == 0:
                                    word_codes_db = []
                                    for word in d_line.words_list:
                                        word = db_scanner.word_code(word)
                                        code = word.code[0] if word.code else "-"
                                        word_ids = getattr(word, "id", [])
                                        from_db = bool(word_ids) and any(
                                            (id_val is not None and id_val != -1) for id_val in word_ids
                                        )
                                        word_codes_db.append({
                                            'word': word.word,
                                            'code': code,
                                            'from_db': from_db
                                        })

                                    line_results[idx]['db_results'].append({
                                        'meter_name': 'No meter match found',
                                        'feet': '',
                                        'word_codes': word_codes_db,
                                        'full_code': ''.join([wc['code'] for wc in word_codes_db]),
                                        'original_line': d_line.original_line
                                    })
            
            except Exception as e:
                error = f"Error processing lines: {str(e)}"

    # print(line_results)
    
    return render_template('test.html', line_results=line_results, error=error, text_input=text_input)


@app.route('/database', methods=['GET', 'POST'])
def database():
    """Route: process multiple lines of poetry using ScansionWithDatabase."""
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
                    # Use database-backed ScansionWithDatabase in this route
                    scanner = ScansionWithDatabase()
                    
                    # Add all lines
                    line_objects = []
                    for line_text in lines:
                        line_obj = Lines(line_text)
                        scanner.add_line(line_obj)
                        line_objects.append(line_obj)

                    # Initialize line_results structure - one entry per line
                    line_results = []
                    for idx, line_obj in enumerate(line_objects):
                        line_results.append({
                            'line_index': idx,
                            'original_line': line_obj.original_line,
                            'results': []
                        })

                    # Use scan_lines() to get all results with crunch() applied
                    # This will mark dominant meters with is_dominant flag
                    all_scan_results = scanner.scan_lines()
                    
                    # Group results by line for display
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
                                
                                line_results[idx]['results'].append({
                                    'meter_name': so.meter_name,
                                    'feet': so.feet,
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

    # Use separate template for database-backed view
    return render_template('database.html', line_results=line_results, error=error, text_input=text_input)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

