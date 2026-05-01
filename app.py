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
from flask import Flask, jsonify, render_template, request

from web.api import get_api_handlers, is_valid_keyword
from aruuz.models import Lines
from aruuz.rhyme.kafiya_dict import KafiyaDict
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
        # In PyInstaller onefile, we bundle the Python project root directly.
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    # In source layout, `python/` is the project root and this file lives in it.
    return Path(__file__).resolve().parent


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

API_HANDLERS = get_api_handlers()
_KAFIYA_DICT: KafiyaDict | None = None
_KAFIYA_LOAD_ERROR: str | None = None
_KAFIYA_PER_PAGE_DEFAULT = 50


def _resolve_kafiya_index_path() -> Path:
    """
    Resolve the filesystem path to the kafiya index using an override and fallback candidates.
    
    If the environment variable KAFIYA_INDEX_PATH is set to a non-empty value, that value is returned (converted to a Path) without checking for existence. Otherwise the function returns the first existing path among these candidates:
    - PROJECT_ROOT/database/kafiya_index.pkl
    - PROJECT_ROOT/aruuz/database/kafiya_index.pkl
    
    If none of the candidates exist, the first candidate (PROJECT_ROOT/database/kafiya_index.pkl) is returned as the canonical fallback.
    
    Returns:
        Path: Resolved path to the kafiya index file.
    """
    env_override = os.getenv("KAFIYA_INDEX_PATH", "").strip()
    if env_override:
        return Path(env_override)

    candidates = [
        PROJECT_ROOT / "database" / "kafiya_index.pkl",
        PROJECT_ROOT / "aruuz" / "database" / "kafiya_index.pkl",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _get_kafiya_dict() -> tuple[KafiyaDict | None, str | None]:
    """
    Load and cache the KafiyaDict index used for kafiya lookups.
    
    Attempts to load the index once and caches either the loaded KafiyaDict or a user-facing error message to avoid repeated load attempts. Subsequent calls return the cached instance or cached error without re-reading the file.
    
    Returns:
        tuple[KafiyaDict | None, str | None]: A tuple where the first element is the loaded KafiyaDict when successful, otherwise `None`; the second element is `None` on success or a human-readable error message when loading failed.
    """
    global _KAFIYA_DICT, _KAFIYA_LOAD_ERROR
    if _KAFIYA_DICT is not None:
        return _KAFIYA_DICT, None
    if _KAFIYA_LOAD_ERROR is not None:
        return None, _KAFIYA_LOAD_ERROR

    index_path = _resolve_kafiya_index_path()
    metadata_path = _resolve_word_metadata_path()
    try:
        _KAFIYA_DICT = KafiyaDict.load(index_path, metadata_path=metadata_path)
        return _KAFIYA_DICT, None
    except Exception:
        logging.getLogger(__name__).exception(
            "Failed to load kafiya index from %s", index_path
        )
        _KAFIYA_LOAD_ERROR = (
            f"Kafiya index could not be loaded from '{index_path}'. "
            "Please verify the file exists and is a valid index."
        )
        return None, _KAFIYA_LOAD_ERROR


def _resolve_word_metadata_path() -> Path:
    """
    Resolve the filesystem path to the word metadata JSON file.
    
    Checks the following in order and returns the first applicable path:
    - The `WORD_METADATA_PATH` environment variable when set to a non-empty value.
    - The first existing candidate among project default locations.
    - The primary canonical candidate (`PROJECT_ROOT/database/word_metadata.json`) if no candidates exist on disk.
    
    Returns:
        Path: Resolved path to the word metadata JSON file.
    """
    env_override = os.getenv("WORD_METADATA_PATH", "").strip()
    if env_override:
        return Path(env_override)

    candidates = [
        PROJECT_ROOT / "database" / "word_metadata.json",
        PROJECT_ROOT / "aruuz" / "database" / "word_metadata.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Render the main UI and process submitted Urdu poetry lines for scansion and meter matching.
    
    On GET renders the index template. On POST reads the form field 'text', validates and splits it into non-empty lines, runs the scansion pipeline to compute per-line results and poem-level dominant bahrs, and populates template context values. If input is empty or processing fails, an error message is provided and result lists are empty or None.
    
    Returns:
        The rendered 'index.html' template with context variables:
        - line_results: per-line scansion results or None
        - error: an error message string or None
        - text_input: the submitted text (trimmed)
        - poem_dominant_bahrs: list of detected dominant bahrs for the poem
        - poem_dominant_bahrs_roman: optional romanized bahrs list
        - poem_dominant_bahrs_info: optional additional bahrs info list
    """
    line_results = None
    error = None
    text_input = ""
    poem_dominant_bahrs = []
    poem_dominant_bahrs_roman = []
    poem_dominant_bahrs_info = []

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
                    poem_dominant_bahrs_roman = scansion_result.get('poem_dominant_bahrs_roman', [])
                    poem_dominant_bahrs_info = scansion_result.get('poem_dominant_bahrs_info', [])
                    
            except Exception as e:
                error = f"Error processing lines: {str(e)}"
                poem_dominant_bahrs = []
                poem_dominant_bahrs_roman = []
                poem_dominant_bahrs_info = []

    return render_template('index.html', line_results=line_results, error=error, text_input=text_input, poem_dominant_bahrs=poem_dominant_bahrs, poem_dominant_bahrs_roman=poem_dominant_bahrs_roman, poem_dominant_bahrs_info=poem_dominant_bahrs_info)


@app.route('/islah', methods=['GET'])
def islah():
    """Islah page: placeholder for correction/suggestions UI."""
    return render_template('islah.html')


@app.route('/qafiya', methods=['GET', 'POST'])
def kafiya():
    """
    Render the Kafiya dictionary lookup page for a single Urdu word.
    
    Reads input from the request form (on POST) or query parameters (on GET). Recognized inputs:
    - text: the Urdu word to look up (trimmed).
    - exact_page, close_page, open_page: 1-based page numbers (integers, clamped to at least 1) for pagination of exact, close, and open-match buckets.
    
    Behavior:
    - If `text` is provided, attempts to load the kafiya index and perform a paginated lookup; on success the lookup result is returned in the template context as `result`.
    - If the kafiya index fails to load or is unavailable, an appropriate user-facing `error` message is provided.
    - If the request is a POST with an empty `text`, sets `error` to "Please enter one Urdu word".
    - If an exception occurs during lookup, sets `error` to "Error processing word: <exception message>".
    
    Returns:
        Rendered template response for 'kafiya.html' with context variables:
        - text_input (str): the submitted word (possibly empty),
        - error (str | None): user-facing error message if any,
        - result (dict | None): lookup results (when available).
    """
    text_input = ""
    error = None
    result = None

    source = request.form if request.method == 'POST' else request.args
    text_input = source.get('text', '').strip()
    exact_page = max(1, source.get('exact_page', default=1, type=int) or 1)
    close_page = max(1, source.get('close_page', default=1, type=int) or 1)
    open_page = max(1, source.get('open_page', default=1, type=int) or 1)

    if text_input:
        kd, load_error = _get_kafiya_dict()
        if load_error:
            error = load_error
        elif kd is None:
            error = "Kafiya lookup is not available right now."
        else:
            try:
                result = kd.lookup(
                    text_input,
                    max_per_bucket=_KAFIYA_PER_PAGE_DEFAULT,
                    page_by_bucket={
                        "exact": exact_page,
                        "close": close_page,
                        "open": open_page,
                    },
                ).to_dict()
            except Exception as e:
                logging.getLogger(__name__).exception(
                    "Error processing kafiya lookup for word: %s", text_input
                )
                error = "An unexpected error occurred while processing the word."
    elif request.method == 'POST':
        error = "Please enter one Urdu word"

    return render_template(
        'kafiya.html',
        text_input=text_input,
        error=error,
        result=result,
    )



@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    """Health check: returns 200 OK when the server is up."""
    return '', 200


@app.route('/api/<path:path_suffix>', methods=['GET', 'POST'])
def api_dispatch(path_suffix: str):
    """
    Discovery-based API router: /api/<segments> -> web.api.<segments_with_underscores>.handle(request).
    Each '/' in the path is converted to '_' for the module name (e.g. /api/meter/dominant -> meter_dominant.py).
    """
    segments = [s for s in path_suffix.split('/') if s]
    if not segments:
        return jsonify({"error": "Not found"}), 404
    if not all(is_valid_keyword(seg) for seg in segments):
        return jsonify({"error": "Not found"}), 404
    handler_key = '_'.join(segments)
    handler = API_HANDLERS.get(handler_key)
    if handler is None:
        return jsonify({"error": "Not found"}), 404
    result = handler(request)
    if isinstance(result, tuple) and len(result) == 2:
        body, status = result
        return jsonify(body), status
    return jsonify(result), 200


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

