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
import sys
from flask import Flask, render_template, request
from aruuz.models import Lines
from aruuz.scansion import Scansion
from aruuz.utils.logging_config import setup_logging

# Configure logging
logs_dir = Path(__file__).parent / 'logs'
setup_logging(logs_dir)

def _resolve_project_root() -> Path:
    """
    Resolve the project root directory.

    - Normal run: `python/app.py` lives in `python/`, so root is parent of that.
    - PyInstaller onefile: files are extracted under `sys._MEIPASS`.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent.parent


PROJECT_ROOT = _resolve_project_root()
WEB_DIR = PROJECT_ROOT / "web"

app = Flask(
    __name__,
    template_folder=str(WEB_DIR / "templates"),
    static_folder=str(WEB_DIR / "static"),
    static_url_path="/static",
)
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['JSON_AS_ASCII'] = False  # Important for Urdu JSON


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
                    # Initialize Scansion object
                    scanner = Scansion()
                    
                    # Add all lines to scanner
                    for line_text in lines:
                        scanner.add_line(Lines(line_text))
                    
                    # Get comprehensive scansion results using the new get_scansion method
                    # This single call handles all processing: meter matching, dominant resolution,
                    # and building the complete result structure
                    scansion_result = scanner.get_scansion()
                    
                    # Extract results for template
                    line_results = scansion_result['line_results']
                    poem_dominant_bahrs = scansion_result['poem_dominant_bahrs']
                    
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

