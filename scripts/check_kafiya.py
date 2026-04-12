import re

PHONETIC_MAP = {
    'ث': 'س',
    'ص': 'س',
    'ذ': 'ز',
    'ض': 'ز',
    'ظ': 'ز',
    'ح': 'ہ',
    'ط': 'ت',
}

# ── Normalization ──────────────────────────────────────────────────────────────

def normalize(word):
    word = re.sub(r'[\u0610-\u061A\u064B-\u065F]', '', word)
    word = re.sub(r'[آأإٱ]', 'ا', word)
    return word.strip()

def phonetic_normalize(word):
    return ''.join(PHONETIC_MAP.get(c, c) for c in word)

def full_normalize(word):
    """Normalize script then apply phonetic map."""
    return phonetic_normalize(normalize(word))

def extract_qaafiya_word(candidate):
    """Guard against radif bleed — always take last token only."""
    tokens = candidate.strip().split()
    return tokens[-1] if tokens else candidate

# ── Suffix utilities ───────────────────────────────────────────────────────────

def longest_common_suffix(w1, w2):
    """Find longest common suffix length between two phonetically normalized words."""
    r1, r2 = w1[::-1], w2[::-1]
    common = 0
    for a, b in zip(r1, r2):
        if a == b:
            common += 1
        else:
            break
    # cap at len-1 so we never match the entire word
    return min(common, len(w1) - 1, len(w2) - 1)

def get_suffix(word, length):
    return word[-length:] if len(word) >= length else word

# ── Main function ──────────────────────────────────────────────────────────────

def detect_qaafiya(candidates: list[tuple[int, str, str]]) -> dict:
    """
    candidates: list of (line_number, full_line, qaafiya_word)

    Returns:
        {
            "qaafiya_suffix": str,        # reference suffix (phonetic form)
            "suffix_length": int,
            "results": [
                {
                    "line_no": int,
                    "full_line": str,
                    "word": str,          # original spelling
                    "status": "reference" | "match" | "phonetic_match" | "flagged",
                    "note": str           # human readable explanation
                }
            ]
        }
    """
    if len(candidates) < 2:
        raise ValueError("Need at least 2 lines to establish a Qaafiya pattern.")

    results = []

    # ── Step 1: establish reference from first two lines (matla) ──────────────
    line_no_1, full_line_1, raw_word_1 = candidates[0]
    line_no_2, full_line_2, raw_word_2 = candidates[1]

    word_1 = extract_qaafiya_word(normalize(raw_word_1))
    word_2 = extract_qaafiya_word(normalize(raw_word_2))

    phonetic_1 = full_normalize(word_1)
    phonetic_2 = full_normalize(word_2)

    suffix_length = longest_common_suffix(phonetic_1, phonetic_2)

    if suffix_length == 0:
        raise ValueError(
            f"Could not establish Qaafiya — "
            f"first two words '{word_1}' and '{word_2}' share no common suffix."
        )

    reference_suffix = get_suffix(phonetic_1, suffix_length)

    # mark both matla lines as reference
    for line_no, full_line, raw_word in [candidates[0], candidates[1]]:
        word = extract_qaafiya_word(normalize(raw_word))
        results.append({
            "line_no": line_no,
            "full_line": full_line,
            "word": word,
            "status": "reference",
            "note": f"Matla — establishes Qaafiya suffix: -{reference_suffix}"
        })

    # ── Step 2: check each remaining line ─────────────────────────────────────
    for line_no, full_line, raw_word in candidates[2:]:
        word = extract_qaafiya_word(normalize(raw_word))
        phonetic_word = full_normalize(word)
        actual_suffix_script = get_suffix(word, suffix_length)
        actual_suffix_phonetic = get_suffix(phonetic_word, suffix_length)

        if actual_suffix_script == reference_suffix:
            # script matches exactly — no phonetic substitution involved
            results.append({
                "line_no": line_no,
                "full_line": full_line,
                "word": word,
                "status": "match",
                "note": f"✅ Script match on -{reference_suffix}"
            })

        elif actual_suffix_phonetic == reference_suffix:
            # doesn't match visually but sounds correct — valid classical Qaafiya
            results.append({
                "line_no": line_no,
                "full_line": full_line,
                "word": word,
                "status": "phonetic_match",
                "note": (
                    f"🔔 Phonetic match — "
                    f"'{actual_suffix_script}' sounds like -{reference_suffix}"
                )
            })

        else:
            results.append({
                "line_no": line_no,
                "full_line": full_line,
                "word": word,
                "status": "flagged",
                "note": (
                    f"❌ Qaafiya break — "
                    f"expected -{reference_suffix}, "
                    f"got -{actual_suffix_script} (phonetic: -{actual_suffix_phonetic})"
                )
            })

    return {
        "qaafiya_suffix": reference_suffix,
        "suffix_length": suffix_length,
        "results": results
    }

# ── Display helper ─────────────────────────────────────────────────────────────

def display_results(detection: dict):
    print(f"\nDetected Qaafiya suffix: -{detection['qaafiya_suffix']}"
          f"  (length: {detection['suffix_length']})")
    print("=" * 50)
    for r in detection["results"]:
        print(f"\nLine {r['line_no']}: {r['full_line']}")
        print(f"  Qaafiya word : {r['word']}")
        print(f"  Status       : {r['note']}")

# ── Test ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    candidates = [
        (1, "دل میں ہے ایک تصویر",         "تصویر"),   # reference
        (2, "وہ آئے زنجیر بکف",            "زنجیر"),   # reference
        (3, "توڑی ہے زندگی کی تقدیر",      "تقدیر"),   # match
        (4, "وہ شخص تھا نظیر",             "نظیر"),    # match
        (5, "کیا ملی مجھے تحریر",          "تحریر"),   # match  (ح → ہ phonetic)
        (6, "اس نے لی میری خبر",           "خبر"),     # flagged — only ر suffix
    ]

    result = detect_qaafiya(candidates)
    display_results(result)