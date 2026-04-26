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
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _scan_codes(scanner: Scansion, normalized_word: str) -> list[str]:
    word_obj = Words()
    word_obj.word = normalized_word
    word_obj.taqti = []

    scanned = scanner.assign_scansion_to_word(word_obj)
    raw_codes = [code.strip() for code in scanned.code if isinstance(code, str)]
    non_empty_codes = [code for code in raw_codes if code]
    return _unique_preserve_order(non_empty_codes)


def _write_json(path: Path, payload: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write("\n")
    temp_path.replace(path)


def _load_existing_metadata(path: Path) -> dict[str, list[str]]:
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
