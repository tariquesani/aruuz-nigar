from __future__ import annotations

import os
from pathlib import Path


def project_root_from_script(script_file: str) -> Path:
    """Return the Python project root for a file under `python/scripts`."""
    return Path(script_file).resolve().parent.parent


def default_index_candidates(python_root: Path) -> list[Path]:
    """
    Candidate index paths in priority order.

    Priority:
    1) python/database/kafiya_index.pkl
    2) python/aruuz/database/kafiya_index.pkl
    """
    return [
        python_root / "database" / "kafiya_index.pkl",
        python_root / "aruuz" / "database" / "kafiya_index.pkl",
    ]


def resolve_index_path(python_root: Path) -> Path:
    """
    Resolve index path with a single shared policy across scripts.

    Order:
    1) KAFIYA_INDEX_PATH env var (if set)
    2) first existing file among default candidates
    3) canonical default path (python/database/kafiya_index.pkl)
    """
    env_override = os.getenv("KAFIYA_INDEX_PATH", "").strip()
    if env_override:
        return Path(env_override)

    candidates = default_index_candidates(python_root)
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0]

