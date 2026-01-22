# Aruuz Nigar — Conceptual Overview

This document is intended as a conceptual introduction for advanced users and developers.

## Purpose and Scope

* Provide a systematic way to analyze the meter of Urdu poetry
* Make classical arūz concepts accessible through computation
* Serve both as a learning aid and an analytical tool
* Focus on correctness, explainability, and openness rather than speed or polish

---

## What Aruuz Nigar Does

* Accepts Urdu poetic text as input
* Infers possible taqti patterns for each line
* Matches inferred patterns against known bahrs
* Identifies one dominant meter across related lines when possible
* Preserves ambiguity instead of forcing a single interpretation

---

## What Aruuz Nigar Does Not Do

* It does not “correct” poetry or judge poetic quality
* It does not assume a single universally correct taqti
* It does not attempt free-verse scansion
* It does not replace human understanding of arūz

---

## Core Concepts

### Aruuz as a Rule-Based System

* Urdu arūz follows structured prosodic rules
* These rules admit flexibility and context-dependent variation
* Aruuz Nigar encodes rules explicitly rather than statistically
* Heuristics are used only where rules permit ambiguity

---

### Words, Syllables, and Taqti

* Words are the smallest meaningful scansion units
* Each word may admit multiple syllabic interpretations
* Taqti represents syllable length as symbolic codes
* Word-level ambiguity is expected and preserved

---

### Meters (Bahr) and Feet (Rukn)

* A bahr is a structured pattern of feet
* Each foot represents a fixed rhythmic sequence
* Meters may admit multiple structural variants
* Matching is based on pattern compatibility, not exact string equality

---

## How the System Thinks

### Determinism and Heuristics

* Given the same input, the engine produces the same results
* Dictionary lookups are preferred where available
* Heuristics are applied only when lexical certainty is unavailable
* All heuristic decisions are traceable and explainable

---

### Ambiguity as a First-Class Outcome

* Multiple valid scans may coexist
* Ambiguity reflects real pronunciation and prosodic variation
* Suppressing ambiguity too early leads to incorrect results
* Resolution is deferred to higher analytical levels

---

### Over-Generation and Later Pruning

* The system deliberately generates more possibilities than needed
* Invalid paths are eliminated during meter matching
* Remaining candidates are scored and compared
* Only implausible interpretations are discarded, not uncertain ones

---

## Levels of Analysis

### Word-Level Analysis

* Assigns one or more scansion codes to each word
* Uses dictionary data, morphology, and heuristics
* Produces the highest degree of ambiguity

---

### Line-Level Analysis

* Combines word-level codes into complete rhythmic paths
* Applies contextual prosodic rules between words
* Matches complete paths against meter definitions
* Produces multiple possible meters per line if applicable

---

### Multi-Line (Sher) Resolution

* Assumes classical consistency of meter across related lines
* Scores meter compatibility across lines
* Selects the most consistent meter as dominant
* Retains per-line detail even after resolution

---

## Interpreting Results

### Multiple Valid Scans

* Multiple outputs do not imply error
* They reflect genuine alternative readings
* Human judgment remains essential in interpretation

---

### Dominant Bahr Selection

* Dominance is a scoring-based decision
* It reflects consistency, not absolute correctness
* Alternate meters are discarded only after comparison

---

### When and Why Results May Differ from Expectation

* Differences may arise from pronunciation assumptions
* Dialectal or poetic license can affect scansion
* Some classical ambiguities have no single resolution
* The system favors explainability over concealment

---

## Intended Users

### Poets and Advanced Readers

* To explore how lines fit classical meters
* To understand why a line scans in a particular way
* To study alternative readings and edge cases

---

### Developers and Researchers

* To study computational modeling of arūz
* To extend or experiment with scansion logic
* To use the engine in non-UI contexts

---

## Where to Go Next

### Pipeline Overview

* For a stage-by-stage conceptual walkthrough of the process

### Engine Execution Flow

* For class- and phase-level understanding of the core engine

### Deep Internal Data Flow

* For function-level tracing and contributor-oriented detail
