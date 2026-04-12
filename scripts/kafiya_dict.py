import sys
import pickle
from collections import defaultdict
from pathlib import Path
"""
CLI wrapper for kafiya dictionary lookup.

Reusable kafiya logic lives in `aruuz.rhyme.kafiya_dict`.
"""

# Allow running this file directly from `python/scripts` by ensuring the
# package root (`python/`) is importable.
_SCRIPT_DIR = Path(__file__).resolve().parent
_PYTHON_ROOT = _SCRIPT_DIR.parent
if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))

from aruuz.rhyme.kafiya_dict import KafiyaDict, KafiyaResult
from aruuz.rhyme.text_utils import full_normalize, normalize_urdu_text
from kafiya_path_policy import resolve_index_path


def build_index(
    words_path: str | Path,
    suffix_lengths: tuple[int, ...] = (1, 2, 3, 4),
) -> dict:
    """Build a suffix index from a newline-delimited Urdu word file."""
    index: dict = defaultdict(set)

    with open(words_path, encoding="utf-8") as fh:
        for raw in fh:
            word = raw.strip()
            if not word:
                continue
            script_word = normalize_urdu_text(word)
            phonetic_word = full_normalize(word)
            for n in suffix_lengths:
                if len(phonetic_word) >= n:
                    index[(n, phonetic_word[-n:])].add(script_word)

    return dict(index)


def build_and_save_index(
    words_path: str | Path,
    output_path: str | Path,
    suffix_lengths: tuple[int, ...] = (1, 2, 3, 4),
) -> None:
    """Build the suffix index and persist it as a pickle file."""
    index = build_index(words_path, suffix_lengths)
    with open(output_path, "wb") as fh:
        pickle.dump(index, fh, protocol=pickle.HIGHEST_PROTOCOL)
    print(f"Saved {len(index)} suffix buckets -> {output_path}")


def display_result(result: KafiyaResult) -> None:
    """Print a KafiyaResult in CLI-friendly grouped format."""
    print(f"\nقافیہ for: {result.query}")
    print("=" * 50)

    buckets = [
        ("🎯 Exact", result.exact, result.suffix_lengths["exact"]),
        ("🔵 Close", result.close, result.suffix_lengths["close"]),
        ("⚪ Open", result.open, result.suffix_lengths["open"]),
    ]

    for label, matches, slen in buckets:
        if not matches:
            continue
        script_words = [m.word for m in matches if m.match_kind == "script"]
        phonetic_words = [m.word for m in matches if m.match_kind == "phonetic"]

        print(f"\n{label}  |  suffix length: {slen}  ({len(matches)} words)")
        if script_words:
            print("  Script  : " + "،  ".join(script_words[:20]))
            if len(script_words) > 20:
                print(f"            … and {len(script_words) - 20} more")
        if phonetic_words:
            print("  Phonetic: " + "،  ".join(phonetic_words[:20]))
            if len(phonetic_words) > 20:
                print(f"            … and {len(phonetic_words) - 20} more")


def main() -> int:
    index_path = (
        Path(sys.argv[1]) if len(sys.argv) > 1 else resolve_index_path(_PYTHON_ROOT)
    )
    urdu_prompt = "لفظ داخل کریں (q to quit): "
    prompt = urdu_prompt
    try:
        if sys.stdout.encoding:
            urdu_prompt.encode(sys.stdout.encoding)
    except UnicodeEncodeError:
        prompt = "Enter word (q to quit): "

    print(f"Loading index from {index_path} …")
    kd = KafiyaDict.load(index_path)
    print("Ready.\n")

    while True:
        try:
            word = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if word.lower() == "q":
            break
        if not word:
            continue
        display_result(kd.lookup(word))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
