"""
Event-driven Explanation Builder (Minimal)

This module generates short, causal, user-facing explanations
for word scansion decisions.

Design principles:
- Explain *why* a scansion is correct, not *how* it was computed
- Use semantic events, not execution steps
- Ignore scanner names, control flow, and pattern checks
- Keep explanations short (1–3 sentences)

Public contract:
- get_explanation(...) signature must remain stable
"""

from typing import Dict, Any, List, Optional, Union
from aruuz.models import Words


class ExplanationBuilder:
    """
    Minimal event-driven explanation builder.

    This class intentionally implements ONLY explanation generation.
    All other public-facing explanation features are deferred.
    """

    def __init__(self):
        self.word: Optional[Words] = None
        self.parts: List[str] = []

    # ------------------------------------------------------------------
    # Public API (contract-preserving)
    # ------------------------------------------------------------------

    def get_explanation(
        self,
        word: Words,
        format: str = "string",
        include_technical: bool = False,  # intentionally ignored
    ) -> Union[str, Dict[str, Any]]:
        """
        Generate a user-facing explanation for a word.

        Args:
            word: Words object to explain
            format: "string" or "structured"
            include_technical: ignored (reserved for future use)

        Returns:
            Explanation as string or structured dict
        """
        self.word = word
        self.parts = []

        # 1. Exceptions table (authoritative, terminal)
        if self._is_exception_word():
            self._add_exception_explanation()
            return self._build(format)

        # 2. Database hija (context, not terminal)
        if self._has_database_hija():
            self._add_hija_context()

        # 3. Compound split (before pattern matching)
        if self._has_compound_split():
            self._add_compound_split_explanation()

        # 4. Decisive heuristic event (may be followed by prosodic transformations)
        has_heuristic = self._add_decisive_heuristic_explanation()

        # 5. Prosodic transformations (can modify codes after pattern matching)
        has_prosodic = self._add_prosodic_explanation()

        # Return if we have any explanation
        if has_heuristic or has_prosodic:
            return self._build(format)

        # 6. Fallback: no explanation
        return self._build(format)

    # ------------------------------------------------------------------
    # Event detection helpers
    # ------------------------------------------------------------------

    def _is_exception_word(self) -> bool:
        if not self.word or not self.word.scansion_generation_steps:
            return False
        return any(
            step.startswith("FOUND_IN_DATABASE_EXCEPTIONS_TABLE")
            for step in self.word.scansion_generation_steps
        )

    def _has_database_hija(self) -> bool:
        return bool(self.word and self.word.taqti)

    def _has_compound_split(self) -> bool:
        """Check if word was split into compound parts."""
        if not self.word:
            return False
        
        # Check scansion_generation_steps first
        if self.word.scansion_generation_steps:
            for step in self.word.scansion_generation_steps:
                if step.startswith("COMPOUND_SPLIT_SUCCEEDED"):
                    return True
        
        # Also check scan_trace_steps
        if self.word.scan_trace_steps:
            for step in self.word.scan_trace_steps:
                stripped = self._strip_prefix(step)
                if stripped.startswith("COMPOUND_SPLIT_SUCCEEDED"):
                    return True
        
        return False

    # ------------------------------------------------------------------
    # Explanation builders
    # ------------------------------------------------------------------

    def _add_exception_explanation(self) -> None:
        """
        Exception-table explanation (authoritative).
        """
        word_text = self.word.word or "word"
        codes = self.word.code or []

        self.parts.append(
            f"The word '{self.word.word}' has a fixed scansion recorded in the exceptions table."
        )

        if len(codes) == 1:
            self.parts.append(
                f"This word is always scanned as {codes[0]}."
            )
        elif len(codes) > 1:
            codes_str = ", ".join(codes)
            self.parts.append(
                f"Accepted scansion codes are: {codes_str}."
            )

    def _add_hija_context(self) -> None:
        """
        Add database-provided syllable split (hija) context.
        """
        hija = self.word.taqti[-1]
        self.parts.append(
            f"The word '{self.word.word}' was found in the database with syllable split (hija/ہِجا) '{hija}'"
        )

    def _add_compound_split_explanation(self) -> None:
        """
        Add explanation for compound word split.
        """
        self.parts.append(
            "The word was split into compound parts; multiple codes may exist."
        )

    def _extract_decisive_event(self) -> Dict[str, Any]:
        """
        Extract decisive facts from trace steps.
        
        Returns:
            Dictionary containing: source, is_muarrab, diacritic, position,
            code, word_length, has_alif_madd, has_alif_madd_start, has_vowel_plus_h_end
        """
        result = {
            "source": None,  # "exceptions" | "heuristic" | None
            "is_muarrab": False,
            "diacritic": None,
            "position": None,
            "code": None,
            "word_length": None,
            "has_alif_madd": False,
            "has_alif_madd_start": False,
            "has_vowel_plus_h_end": False,
        }

        if not self.word:
            return result

        # First, check scansion_generation_steps for exception table hit (highest priority)
        if self.word.scansion_generation_steps:
            for step in self.word.scansion_generation_steps:
                if step.startswith("FOUND_IN_DATABASE_EXCEPTIONS_TABLE"):
                    result["source"] = "exceptions"
                    # Get code from word.code if available
                    if self.word.code:
                        result["code"] = (
                            self.word.code[0] 
                            if isinstance(self.word.code, list) and len(self.word.code) > 0 
                            else self.word.code
                        )
                    return result  # Early return - exceptions are decisive

        # If not exceptions, check scan_trace_steps for heuristic/muarrab patterns
        if not self.word.scan_trace_steps:
            return result

        result["source"] = "heuristic"  # Default to heuristic if we have trace steps

        for raw in self.word.scan_trace_steps:
            step = self._strip_prefix(raw)

            if step.startswith("WORD_IS_MUARRAB"):
                # Check for explicit parameter first
                params = self._parse_params(step)
                if "has_diacritics" in params:
                    result["is_muarrab"] = params.get("has_diacritics", "false").lower() == "true"
                else:
                    # If identifier exists but no parameters, assume true (identifier itself is the signal)
                    result["is_muarrab"] = True

            if step.startswith("AFTER_REMOVING_ARAAB_STRIPPED"):
                params = self._parse_params(step)
                if "length" in params:
                    try:
                        result["word_length"] = int(params["length"])
                    except (ValueError, TypeError):
                        pass

            if step.startswith("CHECKING_DIACRITIC_AT_POSITION"):
                params = self._parse_params(step)
                if params.get("diacritic") == "jazm":
                    result["diacritic"] = "jazm"
                    if "pos" in params:
                        try:
                            result["position"] = int(params["pos"])
                        except (TypeError, ValueError):
                            pass

            if step.startswith("DETECTED_ALIF_MADD_START"):
                result["has_alif_madd_start"] = True
            elif step.startswith("DETECTED_ALIF_MADD"):
                result["has_alif_madd"] = True

            if step.startswith("DETECTED_VOWEL_PLUS_H_END"):
                result["has_vowel_plus_h_end"] = True

            if step.startswith("PATTERN_MATCHED"):
                params = self._parse_params(step)
                if "code" in params:
                    result["code"] = params["code"]
                    # CRITICAL: stop at first decisive match
                    break

        # If no code found in pattern match, try to get from word.code (fallback)
        if not result["code"] and self.word.code:
            result["code"] = (
                self.word.code[0] 
                if isinstance(self.word.code, list) and len(self.word.code) > 0 
                else self.word.code
            )

        return result

    def _add_decisive_heuristic_explanation(self) -> bool:
        """
        Add explanation based on a decisive heuristic event.

        Returns True if a decisive explanation was added.
        """
        facts = self._extract_decisive_event()

        # Short-circuit: if word is from exceptions table, use authoritative explanation
        if facts["source"] == "exceptions":
            # Exceptions are handled earlier in the flow, so this shouldn't happen
            # But handle it gracefully if it does
            return False

        # Fallback: heuristic / muarrab explanation
        if not facts["code"]:
            # No decisive event found - skip explanation
            return False

        # Build explanation
        if facts["is_muarrab"]:
            self.parts.append(
                ", and it was read with vowel marks (diacritics/اعراب)."
            )

        # Position-aware jazm detection
        if facts["diacritic"] == "jazm" and facts["position"] is not None and facts["word_length"] is not None:
            jazm_explanation = self._get_jazm_explanation(facts["position"], facts["word_length"])
            if jazm_explanation:
                self.parts.append(jazm_explanation)

        # Alif madd detection
        if facts["has_alif_madd"] or facts["has_alif_madd_start"]:
            self.parts.append(
                "A long syllable is formed due to alif madd."
            )

        # Vowel + ہ at end detection
        if facts["has_vowel_plus_h_end"]:
            self.parts.append(
                "The final syllable is flexible due to a vowel followed by ہ."
            )

        self.parts.append(
            f"This produces the scansion {facts['code']}."
        )

        return True

    def _get_jazm_explanation(self, position: int, word_length: int) -> Optional[str]:
        """
        Generate position-aware jazm explanation.
        
        Args:
            position: 0-based position of jazm in the word
            word_length: Length of the stripped word
            
        Returns:
            Explanation string or None if position is invalid
        """
        if word_length <= 0:
            return None
        
        # Determine if initial, middle, or final
        if position == 0:
            return "An initial jazm affects syllable closure."
        elif position == word_length - 1:
            return "The word ends in a jazm, closing the final syllable."
        else:
            # Middle position
            return "The middle letter has a jazm, which closes the syllable."

    def _add_prosodic_explanation(self) -> bool:
        """
        Add explanation for prosodic transformations if present.
        """
        if not self.word or not getattr(self.word, "prosodic_transformation_steps", None):
            return False

        steps = self.word.prosodic_transformation_steps
        if not steps:
            return False

        for step in steps:
            if step.startswith("APPLIED_IZAFAT_ADJUSTMENT"):
                self.parts.append(
                    "An izafat adjustment modified the final syllable."
                )
            elif step.startswith("MERGED_AL_WITH_PREVIOUS_WORD"):
                self.parts.append(
                    "The word merged with a following Al (ال) prefix."
                )
            elif step.startswith("EXTENDED_PREVIOUS_WORD_TO_ABSORB_AL"):
                self.parts.append(
                    "The previous word was extended to absorb the Al (ال) prefix."
                )
            elif step.startswith("ADJUSTED_PREVIOUS_WORD_CODE_FOR_CONJUNCTION_ATAF"):
                self.parts.append(
                    "The conjunction 'و' caused a contextual adjustment."
                )
            elif step.startswith("CLEARED_SCANSION_CODES_FOR_CONJUNCTION_AFTER_MERGE"):
                self.parts.append(
                    "Cleared scansion codes for conjunction after merge."
                )
            elif step.startswith("GRAFTED_WITH_FOLLOWING_VOWEL_INITIAL_WORD"):
                self.parts.append(
                    "The word was prosodically grafted to the following word."
                )

        return True

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_prefix(step: str) -> str:
        """
        Remove scanner prefixes like L1S|, L2S|, etc.
        """
        for prefix in ("L1S|", "L2S|", "L3S|", "L4S|", "L5S|"):
            if step.startswith(prefix):
                return step[len(prefix):].strip()
        return step.strip()

    @staticmethod
    def _parse_params(identifier: str) -> Dict[str, str]:
        """
        Parse key=value parameters from an identifier.
        """
        if ":" not in identifier:
            return {}

        param_str = identifier.split(":", 1)[1]
        params: Dict[str, str] = {}

        for pair in param_str.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                params[k.strip()] = v.strip()

        return params

    def _build(self, format: str) -> Union[str, Dict[str, Any]]:
        """
        Finalize explanation output.
        """
        text = " ".join(self.parts).strip()

        if format == "structured":
            return {
                "text": text,
                "events_used": len(self.parts),
            }

        return text
