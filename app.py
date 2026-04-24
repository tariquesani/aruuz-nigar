#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask web application for Urdu poetry scansion and meter matching.

This app provides a web interface to scan complete lines of Urdu poetry
and identify matching meters (bahr).
"""

import logging
import os
import json
from pathlib import Path
import sys
from flask import Flask, jsonify, render_template, request

from web.api import get_api_handlers, is_valid_keyword
from aruuz.models import Lines
from aruuz.rhyme.kafiya_dict import KafiyaDict
from aruuz.rhyme.text_utils import normalize_urdu_text
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
_WORD_METADATA: dict[str, dict[str, object | None]] | None = None
_WORD_METADATA_LOAD_ERROR: str | None = None


def _resolve_kafiya_index_path() -> Path:
    """
    Resolve kafiya index path with shared priority:
    1) KAFIYA_INDEX_PATH env var
    2) first existing default candidate
    3) canonical fallback path
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
    """Load and cache KafiyaDict once; return cached instance or error."""
    global _KAFIYA_DICT, _KAFIYA_LOAD_ERROR
    if _KAFIYA_DICT is not None:
        return _KAFIYA_DICT, None
    if _KAFIYA_LOAD_ERROR is not None:
        return None, _KAFIYA_LOAD_ERROR

    index_path = _resolve_kafiya_index_path()
    try:
        _KAFIYA_DICT = KafiyaDict.load(index_path)
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
    Resolve word metadata path with shared priority:
    1) WORD_METADATA_PATH env var
    2) first existing default candidate
    3) canonical fallback path
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


def _get_word_metadata() -> tuple[dict[str, dict[str, object | None]] | None, str | None]:
    """Load and cache word metadata once; return cached mapping or error."""
    global _WORD_METADATA, _WORD_METADATA_LOAD_ERROR
    if _WORD_METADATA is not None:
        return _WORD_METADATA, None
    if _WORD_METADATA_LOAD_ERROR is not None:
        return None, _WORD_METADATA_LOAD_ERROR

    metadata_path = _resolve_word_metadata_path()
    try:
        with open(metadata_path, encoding="utf-8") as fh:
            loaded = json.load(fh)
        if not isinstance(loaded, dict):
            raise ValueError("word metadata JSON must contain an object at the top level")
        _WORD_METADATA = loaded
        return _WORD_METADATA, None
    except FileNotFoundError:
        _WORD_METADATA_LOAD_ERROR = (
            f"Word metadata could not be loaded from '{metadata_path}'. "
            "Please verify the file exists."
        )
        return None, _WORD_METADATA_LOAD_ERROR
    except Exception:
        logging.getLogger(__name__).exception(
            "Failed to load word metadata from %s", metadata_path
        )
        _WORD_METADATA_LOAD_ERROR = (
            f"Word metadata could not be loaded from '{metadata_path}'. "
            "Please verify the file exists and is valid JSON."
        )
        return None, _WORD_METADATA_LOAD_ERROR


def _attach_word_metadata(
    lookup_result: dict,
    word_metadata: dict[str, dict[str, object | None]] | None,
) -> dict:
    """Attach optional word metadata to match rows without changing grouping."""
    if not word_metadata:
        return lookup_result

    for bucket_name in ("exact", "close", "open"):
        matches = lookup_result.get(bucket_name)
        if not isinstance(matches, list):
            continue
        for match in matches:
            if not isinstance(match, dict):
                continue
            word = match.get("word")
            if not isinstance(word, str):
                continue
            entry = word_metadata.get(normalize_urdu_text(word))
            if entry:
                meaning = entry.get("meaning")
                if isinstance(meaning, str) and meaning:
                    match["meaning"] = meaning

    return lookup_result


@app.route('/', methods=['GET', 'POST'])
def index():
    """Main route: display form and process multiple lines of poetry."""
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


@app.route('/kafiya', methods=['GET', 'POST'])
def kafiya():
    """Kafiya dictionary page: lookup one Urdu word and show grouped results."""
    text_input = ""
    error = None
    result = None

    if request.method == 'POST':
        text_input = request.form.get('text', '').strip()
        if not text_input:
            error = "Please enter one Urdu word"
        else:
            kd, load_error = _get_kafiya_dict()
            if load_error:
                error = load_error
            elif kd is None:
                error = "Kafiya lookup is not available right now."
            else:
                try:
                    result = kd.lookup(text_input).to_dict()
                    word_metadata, _ = _get_word_metadata()
                    result = _attach_word_metadata(result, word_metadata)
                except Exception as e:
                    error = f"Error processing word: {str(e)}"

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

