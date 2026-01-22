# Scansion Data Flow

Documented flow for taking an Urdu sher (two-line couplet) and determining the dominant bahr (meter) using the Python scansion engine.

## 1. High-Level Overview

- **Input**: Sher text (two lines separated by newline).
- **Output**: Dominant bahr name plus supporting scansion metadata per line.
- **Major stages**:
  1. Line cleaning & tokenization.
  2. Word-level scansion code assignment.
  3. Contextual prosodic adjustments.
  4. Code tree construction.
  5. Meter matching & result generation per line.
  6. Dominant bahr resolution across both lines.

## 2. Detailed Flow

Each subsection lists *what happens*, the *function*, and the *file* (with representative line ranges) responsible for the transformation.

### Stage 1 — Sher Input → `Lines` objects

- **What**: Split the sher into separate lines, remove punctuation, normalize characters, and instantiate `Lines`.
- **Functions**:
  - `Lines.__init__()` — `python/aruuz/models.py` L184-L242
  - `clean_line()` / `clean_word()` / `handle_noon_followed_by_stop()` — `python/aruuz/utils/text.py`
- **Notes**:
  - `clean_line()` strips punctuation and zero-width chars.
  - Regex `r'[, ]+'` splits into tokens; Noon+stop clusters are split.
  - Each token becomes a `Words` object with diacritics removed via `remove_araab()`.

### Stage 2 — Word Objects → Initial Codes

- **What**: Assign scansion codes (`=`, `-`, `x`, combinations) to each word via DB lookup plus heuristics.
- **Functions**:
  - `WordScansionAssigner.assign_code_to_word()` — `python/aruuz/scansion/word_scansion_assigner.py` L36-L86
  - `WordLookup.find_word()` — `python/aruuz/database/word_lookup.py`
  - `compute_scansion()` — `python/aruuz/scansion/code_assignment.py` L20-L119
  - Length scanners (`length_one_scan()` … `length_five_scan()`) — `python/aruuz/scansion/length_scanners.py`
- **Notes**:
  - Strategy 1: Database tables (`exceptions`, `mastertable`, `variations`, `Plurals`) provide taqti strings which convert to codes.
  - Strategy 2: Heuristics derive syllable lengths when DB misses.
  - Strategy 3: `_split_compound_word()` attempts to combine DB + heuristic halves; stores Cartesian products of codes/muarrab.

### Stage 3 — Contextual Prosodic Rules

- **What**: Modify codes based on neighboring words and prosodic conventions.
- **Function**: `ProsodicRules.apply_rules()` with helpers for Al, Izafat, Ataf, grafting — `python/aruuz/scansion/prosodic_rules.py`
- **Key behaviours**:
  - **Al (ال)**: If next word starts with “ال”, extend previous code to absorb the definite article.
  - **Izafat (اضافت)**: Adjust endings when zer/izafat markers appear.
  - **Ataf (عطف)**: Handle conjunction “و” by merging with previous word’s cadence.
  - **Word grafting**: When a consonant-ending word joins a following `ا/آ` word, push alternative codes into `word.taqti_word_graft`.
  - For each affected `Words` instance, append human-readable messages to `prosodic_transformation_steps` describing these contextual adjustments.

### Stage 4 — Code Tree Construction

- **What**: Build a tree representing all possible code sequences for the line.
- **Function**: `CodeTree.build_from_line()` — `python/aruuz/tree/code_tree.py` L98-L158
- **Notes**:
  - Root node is synthetic (`code="root"`).
  - For each word, every unique entry in `word.code` and `word.taqti_word_graft` becomes a branch (`codeLocation` node).
  - Children share word indices to cover multiple pronunciations/variants.

### Stage 5 — Meter Pattern Matching (per line)

- **What**: Traverse the code tree, prune codes against meter definitions, and emit matching paths.
- **Functions**:
  - `CodeTree.find_meter()` and `_traverse()` — `python/aruuz/tree/code_tree.py` ~L473-L1019
  - `_is_match()` — compares partial code vs. meter templates (handles `'+'`, `'~'`, `'x'`) — `code_tree.py` L162-L241
  - `_check_code_length()` — validates final code length against meter variations — `code_tree.py` L341-L412
  - Hindi/Zamzama special handling via `PatternTree` — `python/aruuz/tree/pattern_tree.py`
- **Notes**:
  - For each node, tentative code string is compared to all candidate meters; non-matching meters drop off.
  - At leaves, surviving meter indices become part of a `scanPath`.

### Stage 6 — scanPath → `LineScansionResult`

- **What**: Convert each successful path into human-readable scansion info.
- **Function**: `MeterMatcher.match_line_to_meters()` — `python/aruuz/scansion/meter_matching.py` L81-L313
- **Notes**:
  - Extracts ordered `Words` references via `scanPath.location`.
  - Builds `word_taqti`, `full_code`, and interprets meter index into Urdu rukn names using `aruuz.meters`.
  - Returns `LineScansionResult` list per line (one entry per matched meter).

### Stage 7 — Dominant Bahr Resolution (across lines)

- **What**: Combine both misra results and choose the dominant meter.
- **Functions**:
  - `MeterResolver.resolve_dominant_meter()` — `python/aruuz/scansion/scoring.py` L151-L220
  - `MeterResolver.calculate_score()` — `python/aruuz/scansion/scoring.py` L24-L92
- **Notes**:
  - Collect unique meter names from all line results.
  - For each meter, sum ordered-foot matches produced by `calculate_score()` (which checks each variant from `aruuz.meters` via `meter_index()` and `afail()`).
  - Highest total wins; only `LineScansionResult` objects for that meter are returned/flagged as dominant.

## 3. Data & Code Representations

- **Symbols**:
  - `=` long syllable (2 morae).
  - `-` short syllable (1 mora).
  - `x` ambiguous syllable (short or long).
- **Core classes** (from `python/aruuz/models.py`):
  - `Words`: stores `word`, `code[]`, `taqti[]`, `muarrab[]`, `taqti_word_graft[]`, flags (`is_varied`, `modified`), and two explanation lists: `scansion_generation_steps` (base code generation) and `prosodic_transformation_steps` (contextual prosodic changes).
  - `Lines`: wraps `original_line` and `words_list`.
  - `codeLocation`: tree node metadata (`code`, `word_ref`, `code_ref`, `word`).
  - `scanPath`: ordered `codeLocation` list + surviving meter indices.
  - `LineScansionResult`: final per-line output (meter name, feet string/list, word codes, dominance flag).

## 4. File Reference Table

| Stage | Function(s) | File |
| --- | --- | --- |
| Input cleaning & line split | `Lines.__init__()`; `clean_line()`, `clean_word()` | `python/aruuz/models.py`; `python/aruuz/utils/text.py` |
| Word code assignment | `WordScansionAssigner.assign_code_to_word()`; `WordLookup.find_word()`; `compute_scansion()` | `python/aruuz/scansion/word_scansion_assigner.py`; `python/aruuz/database/word_lookup.py`; `python/aruuz/scansion/code_assignment.py` |
| Prosodic adjustments | `ProsodicRules.apply_rules()` | `python/aruuz/scansion/prosodic_rules.py` |
| Tree building | `CodeTree.build_from_line()` | `python/aruuz/tree/code_tree.py` |
| Meter traversal | `CodeTree.find_meter()` / `_traverse()` / `_is_match()` | `python/aruuz/tree/code_tree.py` |
| scanPath → result | `MeterMatcher.match_line_to_meters()` | `python/aruuz/scansion/meter_matching.py` |
| Dominant meter | `MeterResolver.resolve_dominant_meter()`; `calculate_score()` | `python/aruuz/scansion/scoring.py` |

## 5. Flow Diagram

See `scansion_data_flow.mmd` for a Mermaid flowchart mirroring the stages above.
