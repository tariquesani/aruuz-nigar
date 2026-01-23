# Aruuz Nigar — Pure Engine Execution Flow

## Scope

This document describes the **pure Aruuz scansion engine flow**, excluding Flask, web routes, templates, or any UI concerns. It explains how input text is transformed into Aruuz (prosodic scansion) **once it enters the engine layer**, and how data flows across engine components until final scansion results are produced.

This document assumes:
- Input is already available as cleaned line strings
- The caller is responsible for input/output presentation

---

## Engine Entry Point (Conceptual)

**Conceptual entry:**
```
List[str]  →  Aruuz Engine  →  List[scanOutput]
```

In the current codebase, the engine is entered indirectly via Flask. Conceptually, however, the engine begins when:
- A `Scansion` object is created
- One or more `Lines` objects are added
- `scan_lines()` is invoked

---

## Phase 1: Line → Words

### Lines Object Creation

**Class:** `Lines`

**Responsibility:**
- Convert a raw line string into a structured list of words
- Perform text cleaning and normalization

**Flow:**
1. Clean punctuation and zero-width characters
2. Split line into word tokens
3. Normalize word forms
4. Create `Words` objects

**Output:**
- `Lines.original_line`
- `Lines.words_list: List[Words]`

At this stage, **no scansion logic exists**. The engine is still purely lexical.

---

## Phase 2: Engine Initialization

### Scansion Object

**Class:** `Scansion`

**Responsibility:**
- Maintain engine-wide state
- Coordinate scansion phases
- Provide access to database lookup

**Key State:**
- `lst_lines`: all lines to be scanned
- `word_lookup`: database interface (optional)
- Mode flags: `free_verse`, `fuzzy`

No computation occurs here beyond setup.

---

## Phase 3: Line Registration

### Adding Lines

**Method:** `Scansion.add_line()`

**Responsibility:**
- Register `Lines` objects for later processing

This stage merely accumulates input; no scansion is performed yet.

---

## Phase 4: Global Scan Invocation

### scan_lines()

**Method:** `Scansion.scan_lines()`

**Responsibility:**
- Drive the full scansion process
- Aggregate results across all lines

**High-level flow:**
1. Iterate through all registered lines
2. Scan each line independently
3. Collect all scan results
4. Select dominant meter (crunch)

---

## Phase 5: Single-Line Scansion

### scan_line()

This is the **core engine pipeline** for a single poetic line.

### Step 5.1: Word → Code Assignment

**Method:** `Scansion.word_code()`

For each word:
1. If codes already exist, skip
2. Attempt database lookup
3. If found:
   - Convert stored taqti to codes
   - Attach variations if marked `is_varied`
4. If not found:
   - Apply heuristic syllable analysis

**Output:**
- Each `Words` object now contains one or more scansion codes

This step transforms **textual words into symbolic rhythm units**.

---

### Step 5.2: Contextual Word Adjustments

After raw codes are assigned, **inter-word rules** are applied:

1. **Al (ال) handling**
2. **Izafat handling**
3. **Ataf (و) handling**
4. **Word grafting (وصال الف)**

These rules:
- Modify word codes
- Introduce alternative code paths
- Reflect pronunciation-dependent scansion behavior

At the end of this step, ambiguity is fully materialized.

---

## Phase 6: Code Combination Explosion

### CodeTree Construction

**Class:** `CodeTree`

**Responsibility:**
- Represent all possible code combinations for the line

**Concept:**
- Each word may have multiple codes
- Each code introduces a branch
- The tree encodes the Cartesian product of possibilities

This transforms linear code lists into a **search space**.

---

## Phase 7: Meter Matching

### Tree Traversal

**Method:** `CodeTree.find_meter()`

**Responsibility:**
- Traverse all valid code paths
- Match each path against known meter patterns

**Key Behavior:**
- `x` syllables act as wildcards
- PatternTree expands ambiguous matches
- Multiple meters may match a single path

**Output:**
- `scanPath` objects containing:
  - Concrete code sequences
  - Matching meter indices

---

## Phase 8: scanPath → scanOutput

Each valid scan path is converted into a human-meaningful result.

**scanOutput contains:**
- Word-by-word taqti
- Full scansion code
- Meter name
- Feet breakdown

At this point, scansion is **fully resolved for the line**.

---

## Phase 9: Cross-Line Consolidation

### crunch()

**Responsibility:**
- Enforce the classical assumption of a dominant meter
- Score meter consistency across lines
- Discard non-dominant meters

This step transforms multiple local truths into a **global poetic interpretation**.

---

## Phase 10: Engine Output

**Final Output:**
```
List[scanOutput]
```

Each `scanOutput` represents:
- One line
- One meter
- Fully resolved Aruuz scansion

The engine does **no formatting, rendering, or UI decisions**.

---

## Conceptual Summary

```
Lines (text)
  ↓
Words (lexical units)
  ↓
Codes (= - x)
  ↓
CodeTree (combinatorial space)
  ↓
scanPath (valid rhythmic paths)
  ↓
scanOutput (metrical meaning)
```

---

**End of Pure Engine Flow Document**

