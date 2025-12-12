# Phase 1: Core Scansion Engine (No Database, Heuristics Only)

## Overview

**Goal:** Convert the core scansion logic to Python using heuristics only, with no database dependency.

**Timeline:** 5-7 days  
**Deliverable:** Working Python library that can scan Urdu poetry lines and identify meters

---

## Project Structure Setup

```
aruuz_python/
├── README.md
├── requirements.txt          # Dependencies (initially empty or minimal)
├── setup.py                 # Optional, for package installation
├── aruuz/
│   ├── __init__.py
│   ├── scansion.py         # Main scansion engine
│   ├── meters.py            # Meter definitions
│   ├── models.py            # Data classes (Words, Lines, etc.)
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── araab.py        # Diacritical mark removal
│   │   └── text.py         # Text processing utilities
│   └── tree/
│       ├── __init__.py
│       ├── code_tree.py    # Pattern matching tree (Phase 1: basic)
│       └── state_machine.py # State machine (Phase 1: basic)
├── tests/
│   ├── __init__.py
│   ├── test_scansion.py
│   ├── test_meters.py
│   ├── test_utils.py
│   └── test_samples.py     # Test with sample poetry
├── scripts/
│   └── scan_poetry.py     # Simple CLI script
└── examples/
    └── sample_poetry.txt   # Test poetry samples
```

---

## Step-by-Step Conversion Plan

### Step 1: Setup and Foundation (Day 1, Morning)

#### 1.1 Create Project Structure
- [ ] Create directory structure
- [ ] Create `__init__.py` files
- [ ] Create empty `requirements.txt`
- [ ] Create basic `README.md`

#### 1.2 Create Basic Data Models
**File:** `aruuz/models.py`

**Convert from:** `Models/HelperClasses.cs`

**Classes to create:**
- [ ] `Words` class (dataclass)
  - Fields: `word`, `code`, `taqti`, `muarrab`, `length`, `id`, `is_varied`, `error`
  - Methods: None initially (just data structure)
- [ ] `Lines` class
  - Fields: `original_line`, `words_list`
  - Methods: `__init__()` - parse line into words
- [ ] `scanOutput` class (dataclass)
  - Fields: `original_line`, `words`, `meter_name`, `feet`, `word_taqti`
- [ ] `codeLocation` class (dataclass)
  - Fields: `code`, `word_ref`, `code_ref`, `word`, `fuzzy`
- [ ] `scanPath` class
  - Fields: `location` (list), `meters` (list)

**Dependencies:** None (foundation)

---

### Step 2: Utility Functions (Day 1, Afternoon)

#### 2.1 Diacritical Mark Removal
**File:** `aruuz/utils/araab.py`

**Convert from:** `Models/HelperClasses.cs` - `Araab` class

**Functions to create:**
- [ ] `remove_araab(word: str) -> str`
  - Remove all diacritical marks
  - Characters to remove: `\u0651`, `\u0650`, `\u0652`, `\u0656`, `\u0658`, `\u0670`, `\u064B`, `\u064D`, `\u064E`, `\u064F`, `\u0654`
  - Return cleaned word

**Test:** Create `tests/test_utils.py` with basic tests

**Dependencies:** None

---

#### 2.2 Text Processing
**File:** `aruuz/utils/text.py`

**Convert from:** `Models/HelperClasses.cs` - `Lines.Replace()` method

**Functions to create:**
- [ ] `clean_word(word: str) -> str`
  - Handle special character replacements
  - Replace `ئ` at end with `یٔ`
  - Handle `\u0627\u0653` → `آ`
  - Handle `\u06C2` → `\u06C1\u0654`
- [ ] `clean_line(line: str) -> str`
  - Remove punctuation: `,`, `"`, `*`, `'`, `-`, `۔`, `،`, `?`, `!`, etc.
  - Remove zero-width characters
  - Return cleaned line

**Test:** Add tests to `tests/test_utils.py`

**Dependencies:** None

---

### Step 3: Meter Definitions (Day 2, Morning)

#### 3.1 Meter Data Structures
**File:** `aruuz/meters.py`

**Convert from:** `Models/Meters.cs`

**Classes/Functions to create:**
- [ ] `Meters` class (or module-level constants)
  - `NUM_METERS = 129`
  - `NUM_RUBAI_METERS = 12`
  - `NUM_SPECIAL_METERS = 11`
  - `METERS` list - all meter patterns (strings)
  - `METER_NAMES` list - Urdu names
  - `FEET` list - foot patterns
  - `FEET_NAMES` list - foot names in Urdu
  - `RUBAI_METERS` list
  - `RUBAI_METER_NAMES` list
  - `SPECIAL_METERS` list
  - `SPECIAL_METER_NAMES` list

**Helper functions:**
- [ ] `meter_index(meter_name: str) -> List[int]`
  - Find indices of meters matching name
- [ ] `afail(meter: str) -> str`
  - Convert meter pattern to foot names
- [ ] `rukn(code: str) -> str`
  - Convert code to foot name
- [ ] `rukn_code(name: str) -> str`
  - Convert foot name to code

**Test:** Create `tests/test_meters.py`
- Test meter lookup
- Test foot name conversion
- Verify all 129 meters are loaded

**Dependencies:** None (pure data)

---

### Step 4: Word Code Assignment - Heuristics (Day 2, Afternoon - Day 3)

#### 4.1 Basic Length-Based Scansion
**File:** `aruuz/scansion.py` (start with methods)

**Convert from:** `Models/Scansion.cs` - heuristic methods

**Methods to create (in order):**

1. [ ] `length_one_scan(substr: str) -> str`
   - Handle 1-character words
   - If `آ` → return `"="`
   - Otherwise → return `"-"`

2. [ ] `length_two_scan(substr: str) -> str`
   - Handle 2-character words
   - If starts with `آ` → return `"=-"`
   - If ends with vowel+h → return `"x"` (flexible)
   - Otherwise → return `"="`

3. [ ] `length_three_scan(substr: str) -> str`
   - Handle 3-character words
   - Check for special patterns
   - Handle muarrab words
   - Return appropriate code

4. [ ] `length_four_scan(substr: str) -> str`
   - Handle 4-character words
   - Check patterns
   - Return code

5. [ ] `length_five_scan(substr: str) -> str`
   - Handle 5+ character words
   - Break into syllables
   - Return code

6. [ ] `is_vowel_plus_h(char: str) -> bool`
   - Check if character is vowel+h pattern
   - Helper for flexible syllables

7. [ ] `is_muarrab(word: str) -> bool`
   - Check if word has diacritics
   - Helper function

8. [ ] `locate_araab(word: str) -> str`
   - Extract diacritical marks positions
   - Return string of diacritical marks

9. [ ] `assign_code(word: Words) -> str`
   - Main method that calls length-based methods
   - Handles word processing
   - Removes `ھ` and `ں` for scansion
   - Splits taqti into syllables
   - Calls appropriate length method
   - Returns scansion code

**Test:** Create `tests/test_scansion.py`
- Test each length method with known words
- Test `assign_code()` with sample words

**Dependencies:** `utils/araab.py`, `models.py`

---

### Step 5: Line Processing (Day 3, Afternoon)

#### 5.1 Line Parsing
**File:** `aruuz/models.py` (extend `Lines` class)

**Convert from:** `Models/HelperClasses.cs` - `Lines` class

**Methods:**
- [ ] `Lines.__init__(line: str)`
  - Clean line using `utils/text.py`
  - Split into words
  - Create `Words` objects for each word
  - Store in `words_list`

**Test:** Add to `tests/test_scansion.py`
- Test line parsing
- Test word extraction

**Dependencies:** `utils/text.py`, `utils/araab.py`

---

### Step 6: Basic Meter Matching (Day 4, Morning)

#### 6.1 Simple Pattern Matching
**File:** `aruuz/scansion.py` (add methods)

**Convert from:** `Models/codeTree.cs` - `isMatch()` method (simplified)

**Methods to create:**

1. [ ] `is_match(meter: str, code: str) -> bool`
   - Compare meter pattern with code
   - Handle variations (original, +"-", etc.)
   - Check caesura positions
   - Return True if matches

2. [ ] `check_code_length(code: str, meter_indices: List[int]) -> List[int]`
   - Filter meters by code length
   - Check all 4 variations
   - Return list of matching meter indices

**Test:** Add to `tests/test_scansion.py`
- Test with known meter patterns
- Test with sample codes

**Dependencies:** `meters.py`

---

### Step 7: Core Scansion Method (Day 4, Afternoon)

#### 7.1 Main Scansion Logic
**File:** `aruuz/scansion.py` (main class)

**Convert from:** `Models/Scansion.cs` - `scanLines()` method (simplified, no database)

**Class structure:**
```python
class Scansion:
    def __init__(self):
        self.lst_lines = []
        self.num_lines = 0
        self.fuzzy = False
        self.free_verse = False
        self.error_param = 2
        self.meter = []  # List of meter indices to check
    
    def add_line(self, line: Lines):
        # Add line to scan
    
    def scan_lines(self) -> List[scanOutput]:
        # Main scanning method
```

**Methods to implement:**

1. [ ] `add_line(line: Lines)`
   - Add line to `lst_lines`
   - Increment `num_lines`

2. [ ] `word_code(word: Words) -> Words`
   - Assign code to word using heuristics
   - Call `assign_code()`
   - Return word with code assigned

3. [ ] `scan_line(line: Lines, line_index: int) -> List[scanOutput]`
   - Process single line
   - Get codes for all words
   - Match against meters
   - Return possible scan outputs

4. [ ] `scan_lines() -> List[scanOutput]`
   - Main method
   - Process all lines
   - For each line:
     - Get word codes (heuristics)
     - Build code string
     - Match against meters
     - Create scanOutput objects
   - Return list of results

**Test:** Create `tests/test_samples.py`
- Test with sample poetry lines
- Verify meter identification
- Compare with expected results

**Dependencies:** All previous components

---

### Step 8: Simple CLI Interface (Day 5, Morning)

#### 8.1 Command-Line Script
**File:** `scripts/scan_poetry.py`

**Create simple CLI:**
```python
#!/usr/bin/env python3
import sys
from aruuz import Scansion

def main():
    if len(sys.argv) < 2:
        print("Usage: python scan_poetry.py 'poetry text'")
        sys.exit(1)
    
    text = sys.argv[1]
    scanner = Scansion()
    
    # Process lines
    for line in text.split('\n'):
        if line.strip():
            scanner.add_line(line.strip())
    
    # Scan
    results = scanner.scan_lines()
    
    # Display results
    for result in results:
        print(f"Line: {result.original_line}")
        print(f"Meter: {result.meter_name}")
        print(f"Feet: {result.feet}")
        print(f"Code: {''.join(result.word_taqti)}")
        print()

if __name__ == '__main__':
    main()
```

**Test:** Run with sample poetry

**Dependencies:** All scansion components

---

### Step 9: Testing and Validation (Day 5, Afternoon - Day 6)

#### 9.1 Unit Tests
- [ ] Complete `tests/test_utils.py`
  - Test `remove_araab()`
  - Test `clean_word()`
  - Test `clean_line()`

- [ ] Complete `tests/test_meters.py`
  - Test all meter lookups
  - Test foot name conversions
  - Verify data integrity

- [ ] Complete `tests/test_scansion.py`
  - Test all length-based methods
  - Test `assign_code()` with various words
  - Test `is_match()` with known patterns

#### 9.2 Integration Tests
- [ ] Complete `tests/test_samples.py`
  - Test with known poetry samples
  - Compare results with .NET version (if available)
  - Test edge cases

#### 9.3 Sample Poetry Tests
**Create `examples/sample_poetry.txt` with:**
- Simple ghazal lines
- Different meters
- Edge cases

**Test each sample and verify:**
- [ ] Correct meter identification
- [ ] Correct code assignment
- [ ] Correct foot breakdown

---

### Step 10: Documentation and Cleanup (Day 7)

#### 10.1 Code Documentation
- [ ] Add docstrings to all functions/classes
- [ ] Add type hints where helpful
- [ ] Document algorithm decisions

#### 10.2 README
- [ ] Usage instructions
- [ ] Installation steps
- [ ] Example usage
- [ ] Known limitations (no database, heuristics only)

#### 10.3 Code Review
- [ ] Review all code for consistency
- [ ] Check error handling
- [ ] Verify Unicode handling
- [ ] Optimize if needed

---

## Testing Strategy

### Unit Tests (per component)
1. **Utils:** Test each utility function independently
2. **Meters:** Test data loading and lookups
3. **Scansion:** Test each method with known inputs

### Integration Tests
1. **Full pipeline:** Text → Words → Codes → Meters
2. **Sample poetry:** Test with real Urdu poetry
3. **Edge cases:** Empty lines, special characters, etc.

### Validation Tests
1. Compare with .NET results (if possible)
2. Test with known meter poetry
3. Verify accuracy on sample set

---

## Dependencies Between Steps

```
Step 1 (Models) 
    ↓
Step 2 (Utils) → Step 4 (Word Codes)
    ↓                ↓
Step 3 (Meters) → Step 6 (Matching)
    ↓                ↓
Step 5 (Lines) → Step 7 (Scansion)
    ↓                ↓
Step 8 (CLI) ← Step 9 (Testing)
```

---

## Deliverables Checklist

By end of Phase 1, you should have:

- [ ] Working Python package structure
- [ ] All utility functions (araab, text processing)
- [ ] Meter definitions loaded
- [ ] Word code assignment using heuristics
- [ ] Basic meter matching
- [ ] Line processing
- [ ] Main scansion method working
- [ ] Simple CLI script
- [ ] Unit tests for all components
- [ ] Integration tests with sample poetry
- [ ] Documentation (README, docstrings)

---

## Known Limitations (Phase 1)

Document these clearly:
1. **No database lookup** - uses heuristics only
2. **Lower accuracy** for rare/compound words
3. **No fuzzy matching** yet
4. **No free verse analysis** yet
5. **Basic pattern matching** only (no advanced tree traversal)

---

## Success Criteria

Phase 1 is complete when:
- ✅ Can scan simple Urdu poetry lines
- ✅ Identifies correct meters for known poetry
- ✅ All unit tests pass
- ✅ CLI script works end-to-end
- ✅ Code is documented and clean

---

## Next Steps (After Phase 1)

- **Phase 2:** Add SQLite database for word lookup
- **Phase 3:** Enhance meter matching (tree traversal)
- **Phase 4:** Add fuzzy matching
- **Phase 5:** Add free verse analysis

---

## Notes

- This plan focuses on core functionality without database
- Heuristics-based approach for word code assignment
- Simple pattern matching for meter identification
- Can be extended in later phases with database and advanced features
- Keep it simple and working first, optimize later

