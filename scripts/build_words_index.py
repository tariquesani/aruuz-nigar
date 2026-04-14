import pickle
import sys
from collections import defaultdict
from pathlib import Path

try:
    from aruuz.rhyme.text_utils import full_normalize, normalize_urdu_text
except ModuleNotFoundError:
    # Allow running as: python scripts/build_words_index.py
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from aruuz.rhyme.text_utils import full_normalize, normalize_urdu_text
from kafiya_path_policy import resolve_index_path


def build_index(filepath, suffix_lengths=[2, 3, 4]):
    with open(filepath, encoding="utf-8") as f:
        words = [normalize_urdu_text(l.strip()) for l in f if l.strip()]

    index = defaultdict(set)
    for word in words:
        phonetic = full_normalize(word)
        for n in suffix_lengths:
            if len(phonetic) >= n:
                index[(n, phonetic[-n:])].add(word)  # key=phonetic, value=original
    return index

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    python_root = script_dir.parent
    words_path = script_dir / "words.txt"
    output_path = resolve_index_path(python_root)

    print("Building index...")
    index = build_index(str(words_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        pickle.dump(index, f)
    print(f"Done! Indexed {len(index)} suffix entries -> {output_path}")