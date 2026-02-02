# -*- coding: utf-8 -*-
"""
API package: discovery-based routing for /api endpoints.

/api/<path> maps to <path_with_slashes_replaced_by_underscores>.py
(e.g. /api/scan -> scan.py, /api/meter/dominant -> meter_dominant.py).

Each module defines handle(request) -> dict | tuple[dict, int].
"""

import importlib
import logging
import re
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)

_API_DIR = Path(__file__).resolve().parent
_KEYWORD_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]*$")

_handlers_cache: dict[str, Callable] | None = None


def _is_valid_keyword(keyword: str) -> bool:
    return bool(keyword and _KEYWORD_RE.match(keyword))


def get_api_handlers() -> dict[str, Callable]:
    """
    Discover API modules in web/api/*.py (excluding __init__.py), load each,
    and return a map handler_key -> handle.

    Handler key = file stem (e.g. scan.py -> "scan", meter_dominant.py -> "meter_dominant").
    Only stems matching [a-zA-Z][a-zA-Z0-9_]* are used. Result is cached.
    """
    global _handlers_cache
    if _handlers_cache is not None:
        return _handlers_cache

    handlers: dict[str, Callable] = {}
    for path in sorted(_API_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        stem = path.stem
        if not _is_valid_keyword(stem):
            logger.warning("Skip API module %s: invalid keyword %r", path.name, stem)
            continue
        try:
            mod = importlib.import_module(f"web.api.{stem}")
            h = getattr(mod, "handle", None)
            if not callable(h):
                logger.warning("Skip API module %s: no handle() callable", path.name)
                continue
            handlers[stem] = h
        except Exception as e:
            logger.warning("Skip API module %s: %s", path.name, e)

    _handlers_cache = handlers
    return handlers


def is_valid_keyword(keyword: str) -> bool:
    """Check whether keyword is valid (safe for dispatch). Use same rule as discovery."""
    return _is_valid_keyword(keyword)
