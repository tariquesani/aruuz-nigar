import re
import pickle
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
    word = re.sub(r'[\u0610-\u061A\u064B-\u065F]', '', word)
    word = re.sub(r'[آأإٱ]', 'ا', word)
    return word.strip()

def phonetic_normalize(word):
    return ''.join(PHONETIC_MAP.get(c, c) for c in word)

PYTHON_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INDEX_PATH = resolve_index_path(PYTHON_ROOT)


def load_index(path=DEFAULT_INDEX_PATH):
    with open(path, "rb") as f:
        return pickle.load(f)

def find_qaafiya(query, index, suffix_lengths=[1, 2, 3, 4]):
    query_display = normalize(query)
    query_phonetic = phonetic_normalize(query_display)
    results = {}

    for n in suffix_lengths:
        if len(query_phonetic) < n:
            continue
        suffix = query_phonetic[-n:]
        matches = index.get((n, suffix), set()) - {query_display}
        if matches:
            results[suffix] = sorted(matches)
    return query_display, results

def display(query, results):
    print(f"\nقافیہ for: {query}")
    print("=" * 40)
    for suffix in sorted(results, key=len, reverse=True):
        n = len(suffix)
        if n >= 3:
            label = "🎯 Exact"
        elif n == 2:
            label = "🔵 Strong"
        else:
            label = "⚪ Weak"
        print(f"\n{label}  |  suffix: -{suffix}  ({len(results[suffix])} words)")
        print("  " + "،  ".join(results[suffix][:20]))
        if len(results[suffix]) > 20:
            print(f"  ... and {len(results[suffix]) - 20} more")

if __name__ == "__main__":
    print("Loading index...")
    index = load_index()
    print("Ready!\n")

    while True:
        word = input("لفظ داخل کریں (or 'q' to quit): ").strip()
        if word == 'q':
            break
        query, results = find_qaafiya(word, index)
        display(query, results)