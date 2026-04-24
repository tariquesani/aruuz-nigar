"""
Build a normalized Urdu word -> metadata JSON map from the frequent dictionary CSV.

The output is intended as a sidecar metadata file for UI enrichment, not as a
replacement for the kafiya suffix index.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


# Allow running this file directly from `python/scripts` by ensuring the
# package root (`python/`) is importable.
_SCRIPT_DIR = Path(__file__).resolve().parent
_PYTHON_ROOT = _SCRIPT_DIR.parent
if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))

from aruuz.rhyme.text_utils import normalize_urdu_text


def build_metadata_map(csv_path: str | Path) -> dict[str, dict[str, object | None]]:
    """
    Builds a mapping from normalized Urdu words to metadata extracted from a CSV export.
    
    Rows missing an "Urdu word" or an "English meaning of the word" are skipped. Each CSV row's "Urdu word" is normalized; if normalization fails or produces a key already present, the row is ignored (first-row wins). Optional fields are taken from "Roman Urdu Words" (stored as `None` if empty) and "Serial number" (parsed to an integer when it contains only digits, otherwise `None`).
    
    Parameters:
        csv_path (str | Path): Path to the CSV file containing columns
            "Urdu word", "English meaning of the word", "Serial number",
            and "Roman Urdu Words".
    
    Returns:
        dict[str, dict[str, object | None]]: Mapping from normalized Urdu word to a metadata
        dictionary with keys:
          - "meaning" (str): English meaning (always present).
          - "roman" (str | None): Romanized Urdu form or `None`.
          - "frequency_rank" (int | None): Integer rank parsed from "Serial number" or `None`.
    """
    metadata: dict[str, dict[str, object | None]] = {}

    with open(csv_path, encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            raw_word = (row.get("Urdu word") or "").strip()
            if not raw_word:
                continue

            meaning = (row.get("English meaning of the word") or "").strip() or None
            if meaning is None:
                continue

            normalized_word = normalize_urdu_text(raw_word)
            if not normalized_word or normalized_word in metadata:
                continue

            serial_raw = (row.get("Serial number") or "").strip()
            roman = (row.get("Roman Urdu Words") or "").strip() or None

            frequency_rank = None
            if serial_raw.isdigit():
                frequency_rank = int(serial_raw)

            metadata[normalized_word] = {
                "meaning": meaning,
                "roman": roman,
                "frequency_rank": frequency_rank,
            }

    return metadata


def main() -> int:
    """
    Builds a normalized Urdu word → metadata map from the frequent dictionary CSV and writes it to the project's JSON output file.
    
    Creates the output directory if needed, writes UTF-8 JSON (pretty-printed, sorted keys) with a trailing newline, and prints a one-line status message indicating how many entries were saved.
    
    Returns:
        int: Exit status code 0 on success.
    """
    csv_path = _SCRIPT_DIR / "frequent_dictionary_export.csv"
    output_path = _PYTHON_ROOT / "aruuz" / "database" / "word_metadata.json"

    metadata = build_metadata_map(csv_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(metadata, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")

    print(f"Saved {len(metadata)} normalized word metadata entries -> {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
