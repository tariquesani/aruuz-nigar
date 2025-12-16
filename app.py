#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Flask web application for testing Urdu word scansion.

This app provides a web interface to test the scansion engine
with proper RTL (right-to-left) display for Urdu text.
"""

from flask import Flask, render_template, request
from aruuz.models import Words
from aruuz.scansion import assign_code
from aruuz.utils.araab import remove_araab

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-for-testing'
app.config['JSON_AS_ASCII'] = False  # Important for Urdu JSON


def reverse_code_for_rtl(code: str) -> str:
    """
    Reverse the scansion code for RTL display.
    
    Since codes are generated LTR (e.g., "=-"), but Urdu is RTL,
    we reverse the code string for proper RTL display.
    
    Example:
        "=-" -> "-=" (for RTL display)
        "==-" -> "-=="
    
    Args:
        code: The scansion code string (LTR)
        
    Returns:
        Reversed code string for RTL display
    """
    return code[::-1]


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route: display form and process word scanning."""
    result = None
    error = None
    
    if request.method == 'POST':
        word_text = request.form.get('word', '').strip()
        
        if not word_text:
            error = "Please enter an Urdu word"
        else:
            try:
                # Create Words object
                word_obj = Words()
                word_obj.word = word_text
                word_obj.taqti = []
                
                # Calculate length (after removing diacritics and special chars)
                stripped = remove_araab(word_text.replace("\u06BE", "").replace("\u06BA", ""))
                word_obj.length = len(stripped)
                
                # Assign scansion code
                code = assign_code(word_obj)
                
                # Reverse code for RTL display
                code_rtl = reverse_code_for_rtl(code)
                
                result = {
                    'word': word_text,
                    'code': code,
                    'code_rtl': code,
                    'length': word_obj.length
                }
            except Exception as e:
                error = f"Error processing word: {str(e)}"
    
    return render_template('index.html', result=result, error=error)


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

