#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for Urdu poetry scansion and meter matching.

This app provides a web interface to scan complete lines of Urdu poetry
and identify matching meters (bahr).
"""

import logging
import os
from pathlib import Path
from flask import Flask, render_template, request
from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.utils.logging_config import setup_logging
from aruuz.meters import (
    METERS, METERS_VARIED, RUBAI_METERS, SPECIAL_METERS,
    NUM_METERS, NUM_VARIED_METERS, NUM_RUBAI_METERS, NUM_SPECIAL_METERS
) 

# Configure logging
logs_dir = Path(__file__).parent / 'logs'
setup_logging(logs_dir)

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

                    # Step 1: Get all meter matches per line (no per-line resolve_dominant_meter)
                    per_line_candidates = []
                    for idx, line_obj in enumerate(line_objects):
                        candidates = scanner.match_line_to_meters(line_obj, idx)
                        per_line_candidates.append(candidates if candidates else [])
                    
                    # Step 2: Get overall dominant bahr for entire poem (scan_lines across all lines)
                    poem_scan_results = scanner.scan_lines()
                    poem_dominant_bahrs = list({
                        so.meter_name for so in poem_scan_results
                        if so.is_dominant and so.meter_name and so.meter_name != 'No meter match found'
                    })
                    
                    # Step 3: Build line_results structure for template
                    line_results = []
                    for idx, (line_obj, candidates) in enumerate(zip(line_objects, per_line_candidates)):
                        line_result = {
                            'line_index': idx,
                            'original_line': line_obj.original_line,
                            'results': []
                        }
                        
                        if candidates:
                            # Deduplicate by meter_name: keep first occurrence of each (one table per bahr-misra)
                            seen_meter_names = set()
                            unique_candidates = []
                            for so in candidates:
                                if so.meter_name not in seen_meter_names:
                                    seen_meter_names.add(so.meter_name)
                                    unique_candidates.append(so)
                            default_so = next((so for so in unique_candidates if so.meter_name in poem_dominant_bahrs), unique_candidates[0])
                            for so in unique_candidates:
                                feet_list_dict = _build_feet_list_dict(so)
                                meter_pattern = _get_meter_pattern(so, feet_list_dict)
                                line_result['results'].append({
                                    'meter_name': so.meter_name,
                                    'feet': so.feet,
                                    'feet_list': feet_list_dict,
                                    'word_codes': _build_word_codes(so),
                                    'full_code': ''.join(so.word_taqti),
                                    'original_line': so.original_line,
                                    'meter_pattern': meter_pattern,
                                    'is_default': (so is default_so),
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
                                'feet_list': [],
                                'is_default': True,
                            })
                        
                        line_results.append(line_result)
                    
            except Exception as e:
                error = f"Error processing lines: {str(e)}"
                poem_dominant_bahrs = []  # Set empty if error occurred
    
    return render_template('index.html', line_results=line_results, error=error, text_input=text_input, poem_dominant_bahrs=poem_dominant_bahrs)


@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    """Health check: returns 200 OK when the server is up."""
    return '', 200


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

