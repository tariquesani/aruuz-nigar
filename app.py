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
    
    return render_template('index.html', line_results=line_results, error=error, text_input=text_input)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

