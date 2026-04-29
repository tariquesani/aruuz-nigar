"""
Build a normalized Urdu word -> vazn codes JSON map from words.txt.

The output is a sidecar metadata artifact for kafiya ranking, keyed by
normalized Urdu words. Each value is a list of one or more scansion codes.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# Allow running this file directly from `scripts/` by ensuring the package
# root is importable.
_SCRIPT_DIR = Path(__file__).resolve().parent
_PYTHON_ROOT = _SCRIPT_DIR.parent
if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))

from aruuz.models import Words
from aruuz.rhyme.text_utils import normalize_urdu_text
from aruuz.scansion import Scansion


def _unique_preserve_order(items: list[str]) -> list[str]:
    """
    Return a new list containing the first occurrence of each item from the input, preserving the original order.
    
    Returns:
        list[str]: Items from `items` with duplicates removed; each value appears only once in the order of its first appearance.
    """
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scan_codes(scanner: Scansion, normalized_word: str) -> list[str]:
    """
    Extract ordered, de-duplicated scansion codes for a normalized Urdu word.
    
    Uses the provided scansion engine to obtain codes for the given normalized word,
    strips surrounding whitespace, discards non-string and empty entries, and preserves
    the first occurrence order while removing duplicates.
    
    Parameters:
        scanner (Scansion): Scansion engine used to assign scansion to the word.
        normalized_word (str): A normalized Urdu word to be scanned.
    
    Returns:
        list[str]: Scansion codes with whitespace trimmed, empty strings removed,
        and duplicates removed while preserving original order.
    """
    word_obj = Words()
    word_obj.word = normalized_word
    word_obj.taqti = []

    scanned = scanner.assign_scansion_to_word(word_obj)
    raw_codes = [code.strip() for code in scanned.code if isinstance(code, str)]
    non_empty_codes = [code for code in raw_codes if code]
    return _unique_preserve_order(non_empty_codes)


def _write_json(path: Path, payload: dict[str, list[str]]) -> None:
    """
    Write the given mapping as JSON to the destination path atomically, creating parent directories if needed.
    
    The file is written with UTF-8 encoding, sorted keys, an indentation of two spaces, non-ASCII characters preserved, and a final trailing newline. The write is performed to a temporary file which is then moved to the destination to replace any existing file.
    
    Parameters:
        path (Path): Destination file path for the JSON output.
        payload (dict[str, list[str]]): Mapping from normalized words to lists of vazn/scansion codes to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    temp_path.replace(path)


def _load_existing_metadata(path: Path) -> dict[str, list[str]]:
    """
    Load and sanitize an existing word-to-vazn metadata JSON file.
    
    Parameters:
        path (Path): Path to the JSON file containing a mapping from words to lists of vazn/scansion codes.
    
    Returns:
        dict[str, list[str]]: A mapping where each key is a string word and each value is a list of non-empty, whitespace-stripped vazn codes with duplicates removed while preserving original order. Returns an empty dict if the file does not exist or does not contain a valid dict mapping.
    """
    if not path.exists():
        return {}

    with open(path, encoding="utf-8") as fh:
        loaded = json.load(fh)

    if not isinstance(loaded, dict):
        return {}

    out: dict[str, list[str]] = {}
    for key, value in loaded.items():
        if not isinstance(key, str):
            continue
        if not isinstance(value, list):
            continue
        cleaned_codes = [item.strip() for item in value if isinstance(item, str) and item.strip()]
        if cleaned_codes:
            out[key] = _unique_preserve_order(cleaned_codes)
    return out


def build_vazn_map(
    words_path: str | Path,
    *,
    output_path: Path,
    limit: int | None = None,
    progress_every: int = 5000,
    checkpoint_every: int = 1000,
    resume: bool = True,
) -> tuple[dict[str, list[str]], dict[str, int]]:
    """
    Build a mapping from normalized Urdu words to lists of vazn (scansion) codes by scanning words from a text file.
    
    Parameters:
        words_path (str | Path): Path to the input text file containing one Urdu word per line.
        output_path (Path): Path to the JSON file used for resuming and for checkpoint writes.
        limit (int | None): Optional maximum number of unique normalized words to process; `None` means no limit.
        progress_every (int): Print progress every N words (0 disables progress printing).
        checkpoint_every (int): Save intermediate results to `output_path` after every N newly processed words (0 disables checkpointing).
        resume (bool): If true, load and reuse existing metadata from `output_path` and skip already-present words.
    
    Returns:
        tuple[dict[str, list[str]], dict[str, int]]:
            - A dictionary mapping normalized words to de-duplicated, ordered lists of non-empty scansion codes.
            - A stats dictionary containing counts: "input_lines", "normalized_non_empty", "unique_normalized_words",
              "with_codes", "without_codes", "resumed_skips", and "processed_in_run".
    
    Side effects:
        May write checkpoint files to `output_path` (atomic replace) when `checkpoint_every > 0` and prints progress messages according to `progress_every`.
    """
    with open(words_path, encoding="utf-8") as fh:
        raw_words = [line.strip() for line in fh if line.strip()]

    normalized_words = [normalize_urdu_text(word) for word in raw_words]
    normalized_words = [word for word in normalized_words if word]
    unique_words = _unique_preserve_order(normalized_words)

    if limit is not None:
        unique_words = unique_words[:limit]

    existing = _load_existing_metadata(output_path) if resume else {}
    if existing:
        print(f"Loaded existing metadata: {len(existing)} words from {output_path}")

    scanner = Scansion()
    out: dict[str, list[str]] = dict(existing)
    empty_code_count = 0
    resumed_skip_count = 0
    processed_in_run = 0

    total = len(unique_words)
    for idx, word in enumerate(unique_words, start=1):
        if word in out:
            resumed_skip_count += 1
            if progress_every > 0 and idx % progress_every == 0:
                print(
                    f"Scanned {idx}/{total} words... "
                    f"(new={processed_in_run}, resumed_skips={resumed_skip_count})"
                )
            continue

        codes = _scan_codes(scanner, word)
        processed_in_run += 1
        if codes:
            out[word] = codes
        else:
            empty_code_count += 1

        if checkpoint_every > 0 and processed_in_run % checkpoint_every == 0:
            _write_json(output_path, out)
            print(
                f"Checkpoint saved after {processed_in_run} new words "
                f"(total_saved={len(out)})"
            )

        if progress_every > 0 and idx % progress_every == 0:
            print(
                f"Scanned {idx}/{total} words... "
                f"(new={processed_in_run}, resumed_skips={resumed_skip_count})"
            )

    stats = {
        "input_lines": len(raw_words),
        "normalized_non_empty": len(normalized_words),
        "unique_normalized_words": len(unique_words),
        "with_codes": len(out),
        "without_codes": empty_code_count,
        "resumed_skips": resumed_skip_count,
        "processed_in_run": processed_in_run,
    }
    return out, stats


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for the word→vazn metadata builder.
    
    Options:
    - words_path: Path to words.txt (default: scripts/words.txt)
    - output_path: Path to output JSON file (default: aruuz/database/word_vazn_metadata.json)
    - limit: Optional maximum number of unique normalized words to process
    - progress_every: Print progress every N processed words (0 disables)
    - checkpoint_every: Persist output every N newly processed words (0 disables)
    - no_resume: If set, ignore existing output and recompute from scratch
    
    Returns:
        argparse.Namespace: Parsed arguments with attributes `words_path`, `output_path`, `limit`, `progress_every`, `checkpoint_every`, and `no_resume`.
    """
    parser = argparse.ArgumentParser(
        description="Build normalized word -> list[vazn code] JSON metadata.",
    )
    parser.add_argument(
        "--words-path",
        type=Path,
        default=_SCRIPT_DIR / "words.txt",
        help="Path to words.txt (default: scripts/words.txt)",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=_PYTHON_ROOT / "aruuz" / "database" / "word_vazn_metadata.json",
        help="Path to output JSON file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max number of unique normalized words to process",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=5000,
        help="Print progress every N processed words (0 disables progress prints)",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=1000,
        help="Persist output every N new words processed (0 disables checkpoints)",
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore existing output file and recompute from scratch",
    )
    return parser.parse_args()


def main() -> int:
    """
    Run the CLI: parse arguments, build the vazn mapping, write the output file, and print a summary.
    
    Returns:
        exit_code (int): Process exit code (0 for success).
    """
    args = parse_args()

    vazn_map, stats = build_vazn_map(
        args.words_path,
        output_path=args.output_path,
        limit=args.limit,
        progress_every=args.progress_every,
        checkpoint_every=args.checkpoint_every,
        resume=not args.no_resume,
    )

    _write_json(args.output_path, vazn_map)

    print(f"Saved {len(vazn_map)} words -> {args.output_path}")
    print(
        "Stats: "
        f"input_lines={stats['input_lines']}, "
        f"normalized_non_empty={stats['normalized_non_empty']}, "
        f"unique_normalized_words={stats['unique_normalized_words']}, "
        f"with_codes={stats['with_codes']}, "
        f"without_codes={stats['without_codes']}, "
        f"resumed_skips={stats['resumed_skips']}, "
        f"processed_in_run={stats['processed_in_run']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
