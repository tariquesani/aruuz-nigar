# Ambiguity in Aruuz Nigar

This document is intended to clarify interpretation of results rather than engine mechanics.

## Purpose of This Document

* Explain why ambiguity is inherent in Urdu arūz
* Clarify how and where ambiguity arises in Aruuz Nigar
* Distinguish expected ambiguity from genuine limitations
* Help users interpret results correctly and confidently

---

## Why Ambiguity Exists in Urdu Arūz

* Urdu arūz is based on pronunciation, not spelling
* Pronunciation varies by context, convention, and reader
* Classical prosody allows multiple valid readings of the same line
* Ambiguity is a property of the poetic system, not a computational artifact

---

## Ambiguity as a Design Principle

* Aruuz Nigar treats ambiguity as meaningful information
* The engine avoids forcing early decisions
* Multiple interpretations are preserved where rules permit
* Certainty is introduced only when structural evidence is sufficient

---

## Types of Ambiguity Encountered

### Lexical Ambiguity (Word-Level)

* A single word may admit multiple syllabic patterns
* Dictionary entries may contain variants
* Heuristic analysis may produce multiple valid outcomes
* Word-level ambiguity is common and expected

---

### Contextual Ambiguity (Inter-Word)

* Pronunciation may change based on neighboring words
* Classical prosodic rules introduce conditional variations
* Word joins and elisions can produce alternate rhythmic paths
* Contextual ambiguity may increase, not decrease, possibilities

---

### Metrical Ambiguity (Line-Level)

* A complete rhythmic pattern may fit more than one meter
* Closely related meters may share structural prefixes
* Multiple meters may remain valid even after full analysis
* This reflects classical overlap, not analytical failure

---

## How Aruuz Nigar Handles Ambiguity

### Intentional Over-Generation

* The engine generates all plausible scansion possibilities
* No valid interpretations are discarded prematurely
* Over-generation ensures completeness of analysis

---

### Constraint-Driven Pruning

* Invalid interpretations are eliminated by meter constraints
* Pruning occurs gradually as structure accumulates
* Only interpretations that violate prosodic rules are removed

---

### Late Resolution

* Ambiguity is resolved only after full line or multi-line context
* Word-level uncertainty is evaluated at meter level
* Decisions are postponed until meaningful comparison is possible

---

## Dominant Bahr and Ambiguity

### What “Dominant” Means

* Dominance is a scoring-based preference
* It reflects consistency across related lines
* It does not imply absolute correctness

---

### What Dominant Does Not Mean

* It does not mean alternate meters are wrong
* It does not eliminate all ambiguity in interpretation
* It does not override classical permissibility

---

## When Ambiguity Is Expected

* Classical poetry with flexible pronunciation
* Lines with optional joins or elisions
* Meters with overlapping structural forms
* Words with well-known variant readings

---

## When Ambiguity May Indicate a Limitation

* Rare or highly dialectal vocabulary
* Modern poetic forms outside classical arūz
* Incomplete lexical coverage
* Known unsupported or weakly supported meters

---

## How Users Should Interpret Results

* Multiple results should be read as interpretive space
* Human judgment remains essential in choosing among alternatives
* Consistency across lines is more significant than isolated matches
* Ambiguity should be explored, not dismissed

---

## Common Misconceptions

### “More results mean lower confidence”

* False: multiple results often indicate legitimate flexibility

### “There must be exactly one correct scansion”

* False: classical arūz permits multiple valid readings

### “Dominant bahr is the only correct answer”

* False: dominance reflects preference, not exclusivity

---

## Relationship to Other Documents

* Complements *Conceptual Overview*
* Clarifies interpretation of *Pipeline Overview*
* Does not describe execution mechanics or code structure
* Should be read before assuming incorrect behavior
