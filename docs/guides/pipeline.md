# Aruuz Nigar — Scansion Pipeline Overview

This document assumes familiarity with basic arūz concepts and focuses on execution flow.

## Purpose of This Document

* Describe how Aruuz Nigar processes poetic text from input to scansion output
* Present the engine pipeline at a conceptual but accurate level
* Provide a mental model consistent with the actual execution flow
* Bridge high-level concepts and detailed internal documentation

---

## Pipeline at a Glance

* Input is processed through a sequence of constrained transformations
* Ambiguity is introduced early and resolved late
* Combination and pruning occur together, not as separate phases
* The pipeline is driven by structural constraints, not guesswork

---

## Stage 1: Input Normalization

* Raw poetic text is cleaned of punctuation and non-visible characters
* Characters are normalized to consistent forms
* Each line is treated as an independent analytical unit
* No rhythmic or metrical assumptions are made at this stage

---

## Stage 2: Tokenization into Words

* Each normalized line is split into lexical word units
* Word boundaries follow orthographic conventions
* Each word becomes a structured object for later analysis
* Diacritics, when present, are preserved as optional cues

---

## Stage 3: Word-Level Scansion

* Each word is analyzed in isolation
* Possible syllabic interpretations are inferred
* Long, short, and ambiguous syllables are represented symbolically
* Multiple scansion codes per word are expected and preserved
* Dictionary knowledge is preferred where available, heuristics fill gaps

---

## Stage 4: Contextual Prosodic Adjustment

* Inter-word prosodic rules are applied
* Pronunciation-dependent effects modify scansion possibilities
* Additional variants may be introduced based on context
* No scansion possibilities are discarded at this stage

---

## Stage 5: CodeTree Construction and Search Space Formation

* Word-level scansion variants are organized into a tree structure
* Each branch represents a complete rhythmic possibility for the line
* The tree encodes the full combinatorial search space implicitly
* No explicit Cartesian product of codes is materialized

---

## Stage 6: Tree Traversal and Meter Constraint Application

* The code tree is traversed depth-first
* Partial rhythmic paths are continuously checked against meter constraints
* Incompatible meters are eliminated as soon as constraints are violated
* Ambiguity is preserved where classical rules permit flexibility
* Matching and pruning occur simultaneously during traversal

---

## Stage 7: Line-Level Scansion Results

* Each surviving traversal path produces a complete line-level result
* Results include:

  * Word-by-word taqti
  * Complete rhythmic pattern
  * One or more matching meters
* Multiple valid results per line may coexist

---

## Stage 8: Dominant Meter Resolution

* A classical assumption of meter consistency across related lines is applied
* Candidate meters are scored across all analyzed lines
* Structural consistency is prioritized over local or partial matches
* All non-dominant meters are explicitly discarded

---

## Stage 9: Final Output

* Output consists of structured scansion results
* Each result is traceable to the decisions made during the pipeline
* The engine makes no assumptions about presentation or formatting
* Consumers are free to render, visualize, or post-process results

---

## Key Design Properties of the Pipeline

### Deterministic Execution

* The same input always produces the same results
* No probabilistic or stochastic mechanisms are used

### Late Commitment

* Uncertainty is preserved until sufficient structural context exists
* Early decisions are avoided wherever possible

### Explainability

* Each transformation stage has a clear rationale
* Intermediate representations are inspectable
* Final results can be traced back through the pipeline

---

## Relationship to Other Documents

* This document explains **what happens, and when**
* It does not describe **how individual functions are implemented**
* For engine phase-level detail, see *Pure Engine Execution Flow*
* For function-level tracing, see *Scansion Data Flow*

