import re
import pickle
from collections import defaultdict
from pathlib import Path
from kafiya_path_policy import resolve_index_path

PHONETIC_MAP = {
    'ث': 'س',
    'ص': 'س',
    'ذ': 'ز',
    'ض': 'ز',
    'ظ': 'ز',
    'ح': 'ہ',
    'ط': 'ت',
}

def normalize(word):
    word = re.sub(r'[\u0610-\u061A\u064B-\u065F]', '', word)  # remove diacritics
    word = re.sub(r'[آأإٱ]', 'ا', word)                        # normalize alef variants
    return word.strip()

def phonetic_normalize(word):
    return ''.join(PHONETIC_MAP.get(c, c) for c in word)

def build_index(filepath, suffix_lengths=[1, 2, 3, 4]):
    with open(filepath, encoding="utf-8") as f:
        words = [normalize(l.strip()) for l in f if l.strip()]

    index = defaultdict(set)
    for word in words:
        phonetic = phonetic_normalize(word)
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