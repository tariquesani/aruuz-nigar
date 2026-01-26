"""
Scoring and Resolution

Stateless class with static methods for calculating meter match scores
and resolving dominant meters.
"""

import math
from collections import Counter
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from aruuz.models import LineScansionResult, LineScansionResultFuzzy

from .explain_logging import get_explain_logger

from aruuz.meters import METERS, METERS_VARIED, RUBAI_METERS, SPECIAL_METERS, SPECIAL_METER_NAMES, meter_index, afail

# Meter preference justification:
# These weights are used ONLY to break ties where multiple meters
# match a line equally well structurally.
#
# Rationale:
# - رمل (especially مثمن محذوف) is statistically and stylistically
#   dominant in ghazal and nazm with smooth, conversational flow.
# - ہزج and کامل are common but slightly more rhythmically marked.
# - منسرح is structurally permissive and often matches incidentally,
#   but is stylistically less likely unless strongly signaled.
#
# Therefore, preference reflects idiomatic likelihood,
# not structural superiority.
# A final list would look like this:
#
# METER_PREFERENCE = {
#     "رمل مثمن محذوف": 3.0,        # Ramal Musamman Mahzuf
#     "رمل مثمن": 2.5,              # Ramal Musamman
#     "ہزج مثمن": 2.0,              # Hazaj Musamman
#     "کامل": 1.5,                  # Kamil (Musamman)
#     "منسرح مثمن مطوی مکسوف": 1.0, # Mansurah Musamman Mutawi Maksuf

#     # Common classical meters (Ghalib, Mir, etc.)
#     "خفیف مثمن": 2.3,             # Khafiif Musamman
#     "رجز مثمن سالم": 2.2,         # Rajaz Musamman Salim
#     "متقارب مثمن": 1.8,           # Mutaqarib Musamman
#     "متدارک مثمن": 1.4,           # Mutadarak Musamman

#     # Frequent variants
#     "بسیط مثمن محذوف": 1.2,       # Baseet Musamman Mahzuf
#     "طویل مثمن": 1.1,             # Taweel Musamman
#     "وافر مثمن": 1.0,             # Wafir Musamman
#     "مضارع مثمن": 0.9,            # Muzari Musamman
#     "رمل مثمن مکفوف": 0.8,        # Ramal Musamman Makfuf
#     "ہزج مثمن اخرب": 0.7,         # Hazaj Musamman Akhrab
# }
#
# Simplified version:
METER_PREFERENCE = {
    "رمل مثمن محذوف": 3.0,
    "رمل مثمن": 2.5,
    "ہزج مثمن": 2.0,
    "کامل": 1.5,
    "منسرح مثمن مطوی مکسوف": 1.0,
}


class MeterResolver:
    """
    Stateless class for scoring and resolving meters.
    
    All methods are static methods (pure logic).
    """
    
    @staticmethod
    def calculate_score(meter: str, line_feet: str) -> int:
        """
        Calculate score for how well a line matches a meter.
        
        This method evaluates how well a poetry line's feet match against all
        variants of a given meter pattern. It parses the line's feet, retrieves
        all meter variants for the given meter name, and evaluates each variant
        separately to find the best match.
        
        The score represents the number of feet that match in the correct order
        against the best matching meter variant. Each meter variant is evaluated
        independently, and the maximum score across all variants is returned.
        
        Args:
            meter: Meter name string (e.g., "مفعولن مفعولن مفعولن مفعولن")
            line_feet: Space-separated string of feet from the scanned line
                      (e.g., "مفعولن مفعولن مفعولن مفعولن")
        
        Returns:
            Integer score representing the number of matching feet in correct order.
            Returns 0 if:
            - No meter variants found for the given meter name
            - No meter variant has matching length with the line
            - No feet match in order
            Otherwise returns the maximum score (1 to number of feet) across all variants.
        
        Note:
            This method evaluates each meter variant separately. A meter name may
            have multiple variants (e.g., with different '+' positions), and the
            score is calculated for each variant independently. The method requires
            that the line feet and meter feet have the same length (hard structural
            constraint) before evaluating the match.
        """
        meter_indices = meter_index(meter)

        if not meter_indices:
            return 0

        # Parse line feet (DO NOT deduplicate)
        line_arkaan = []
        for s in line_feet.split(' '):
            s = s.strip()
            if s:
                line_arkaan.append(s)

        best_score = 0

        # IMPORTANT CHANGE: evaluate EACH meter variant separately
        for m_idx in meter_indices:
            if m_idx >= len(METERS):
                continue

            # Get feet for THIS meter variant only
            meter_feet = []
            for s in afail(METERS[m_idx]).split(' '):
                s = s.strip()
                if s:
                    meter_feet.append(s)

            # Hard structural constraint
            if len(line_arkaan) != len(meter_feet):
                continue

            score = MeterResolver.ordered_match_count(line_arkaan, meter_feet)
            best_score = max(best_score, score)

        return best_score
    
    @staticmethod
    def ordered_match_count(line_feet: List[str], meter_feet: List[str]) -> int:
        """
        Count how many feet from line_feet appear in meter_feet in correct relative order.
        
        This method implements a greedy matching algorithm that counts consecutive
        matching feet starting from the beginning. It iterates through line_feet
        and tries to find each foot in meter_feet, maintaining the relative order.
        The matching stops at the first foot that cannot be found in the correct
        position, and returns the count of successfully matched feet up to that point.
        
        The algorithm ensures that:
        1. Feet must match exactly (string equality)
        2. Feet must appear in the same relative order in both lists
        3. Matching is greedy (each line foot is matched to the first available
           meter foot that hasn't been matched yet)
        4. Matching stops at the first failure (no backtracking)
        
        Args:
            line_feet: List of foot strings from the scanned poetry line
                      (e.g., ["مفعولن", "مفعولن", "فاعلن"])
            meter_feet: List of foot strings from the meter pattern
                       (e.g., ["مفعولن", "مفعولن", "مفعولن", "مفعولن"])
        
        Returns:
            Integer count of feet that matched in order (0 to len(line_feet)).
            Returns 0 if the first foot doesn't match, or the number of consecutive
            matching feet from the start of the list.
        
        Example:
            If line_feet = ["مفعولن", "مفعولن", "فاعلن"]
            and meter_feet = ["مفعولن", "مفعولن", "مفعولن", "مفعولن"]
            Returns 2 (first two feet match)
            
            If line_feet = ["مفعولن", "فاعلن", "مفعولن"]
            and meter_feet = ["مفعولن", "مفعولن", "فاعلن"]
            Returns 1 (only first foot matches, second doesn't match at position 1)
        """
        count = 0
        j = 0
        matches = []

        for f in line_feet:
            found_match = False
            while j < len(meter_feet):
                if f == meter_feet[j]:
                    count += 1
                    matches.append(f"'{f}' at position {j}")
                    j += 1
                    found_match = True
                    break
                j += 1
            if not found_match:
                # No match found for this foot, stop counting
                break
        return count
    
    @staticmethod
    def resolve_dominant_meter(results: List['LineScansionResult']) -> List['LineScansionResult']:
        """
        Consolidate multiple meter matches and return only those matching dominant meter.

        Algorithm:
        0. Perform count-based dominance.
        - Special meters (listed in SPECIAL_METER_NAMES) are grouped by their
            conceptual bahr (text before '/'); their counts are summed.
        - Non-special meters compete individually.
        - The candidate (group or individual) with the highest count > 1 is selected.
        - If a group is selected, the representative meter is the group member with
            the highest individual count.
        1. If no candidate has count > 1, fall back to score-based selection.
        2. Score each meter by summing calculateScore() for all matching lines
        3. Sort scores and meter names together (maintain pairing)
        4. Select meter with highest score
        5. If multiple meters have same highest score, select based on METER_PREFERENCE
        6. Return all LineScansionResult objects matching the selected meter
        
        Args:
            results: List of LineScansionResult objects (multiple matches per line)
            
        Returns:
            List of LineScansionResult objects for the dominant meter only
        """
        if not results:
            return []

        # Count-based dominance: prefer the meter (or special-meter group) that appears
        # in the most lines. Special meters (SPECIAL_METER_NAMES) are grouped by
        # conceptual bahr (part before '/'); their line-match counts are summed when
        # competing. Non-special meters compete individually. Foot-match score is used
        # only as fallback when no candidate has count > 1.
        c = Counter(item.meter_name for item in results if item.meter_name)

        # Build special-meter groups: conceptual bahr = name.split('/', 1)[0].strip()
        group_count = {}
        group_members = {}
        for m, cnt in c.items():
            if m in SPECIAL_METER_NAMES:
                bahr = m.split('/', 1)[0].strip()
                group_count[bahr] = group_count.get(bahr, 0) + cnt
                group_members.setdefault(bahr, []).append(m)

        # Candidates: (score, 'individual'|'group', meter_or_bahr)
        candidates = []
        for m, cnt in c.items():
            if m not in SPECIAL_METER_NAMES:
                candidates.append((cnt, 'individual', m))
        for bahr, cnt in group_count.items():
            candidates.append((cnt, 'group', bahr))

        max_score = max((s for s, _, _ in candidates), default=0)

        if max_score <= 1:
            final_meter = None
        else:
            tied = [(s, typ, x) for s, typ, x in candidates if s == max_score]
            tied_individuals = [x for s, typ, x in tied if typ == 'individual']
            tied_groups = [x for s, typ, x in tied if typ == 'group']

            if tied_individuals:
                # Tie: group vs regular → regular wins.
                if len(tied_individuals) == 1:
                    final_meter = tied_individuals[0]
                else:
                    # Tie among non-special meters → METER_PREFERENCE.
                    final_meter = max(tied_individuals, key=lambda m: METER_PREFERENCE.get(m, 0.0))
            else:
                # Only groups. Tie: group vs group → بحرِ ہندی wins.
                winner_bahr = (
                    tied_groups[0] if len(tied_groups) == 1
                    else ("بحرِ ہندی" if "بحرِ ہندی" in tied_groups else tied_groups[0])
                )
                members = group_members[winner_bahr]
                # Representative: max c[m] in group; tie → first in SPECIAL_METER_NAMES.
                final_meter = min(members, key=lambda m: (-c[m], SPECIAL_METER_NAMES.index(m)))

            explain_logger = get_explain_logger()
            counts_str = ', '.join(f"{name}={cnt}" for name, cnt in c.most_common())
            explain_logger.info(f"SELECT | Dominance | Selected '{final_meter}' | By line count: {counts_str}")

        if final_meter is None:
            # Fallback: score-based selection (sum of foot-match scores, then METER_PREFERENCE)
            # Collect unique meter names (matching C# logic)
            meter_names = []
            for item in results:
                if item.meter_name:
                    # Check if already in list
                    found = False
                    for existing in meter_names:
                        if existing == item.meter_name:
                            found = True
                            break
                    if not found:
                        meter_names.append(item.meter_name)

            if not meter_names:
                return []

            # Score each meter
            explain_logger = get_explain_logger()
            scores = [0.0] * len(meter_names)
            for i, meter_name in enumerate(meter_names):
                for item in results:
                    if item.meter_name == meter_name:
                        score = MeterResolver.calculate_score(meter_name, item.feet)
                        scores[i] += score
                # Log scoring for each meter
                explain_logger.info(f"DECISION | Dominance scoring | Meter '{meter_name}': score {scores[i]}")

            # Sort scores and meter names together (maintain pairing)
            # Create list of tuples, sort by score, then extract
            paired = list(zip(scores, meter_names))

            max_score = max(scores)
            candidates = [
                meter_name
                for score, meter_name in paired
                if score == max_score
            ]

            if len(candidates) == 1:
                final_meter = candidates[0]
            else:
                final_meter = max(
                    candidates,
                    key=lambda m: METER_PREFERENCE.get(m, 0.0)
                )

            # Log final dominance selection with all scores
            scores_str = ', '.join([f"{meter_name}={score}" for score, meter_name in paired])
            explain_logger.info(f"SELECT | Dominance | Selected '{final_meter}' | Scores: {scores_str}")

        if not final_meter:
            return []
        
        # Filter results: return only LineScansionResult objects matching final_meter
        filtered_results = []
        for item in results:
            if item.meter_name == final_meter:
                filtered_results.append(item)
        
        return filtered_results
    
    @staticmethod
    def resolve_dominant_meter_fuzzy(results: List['LineScansionResultFuzzy']) -> List['LineScansionResultFuzzy']:
        """
        Consolidate fuzzy matching results and return only those matching the best meter.
        
        Algorithm (matching C# crunchFuzzy):
        1. Collect all unique meter names from results
        2. For each meter, calculate aggregate score using logarithmic averaging:
           score = exp(sum(log(scores)) / count) - subtract
           where subtract is the count of zero scores
        3. Handle score == 0 case (add 1 before log, increment subtract)
        4. Sort meters by score (lowest is best for Levenshtein distance)
        5. Select meter with best (lowest) score
        6. Filter results to return only those matching the selected meter
        7. Handle special IDs (-2 for rubai, < 0 for special meters)
        
        Args:
            results: List of LineScansionResultFuzzy objects (multiple matches per line)
            
        Returns:
            List of LineScansionResultFuzzy objects for the best meter only
        """
        if not results:
            return []
        
        # Collect unique meter names (matching C# logic)
        meter_names = []
        for item in results:
            if item.meter_name:
                # Check if already in list
                found = False
                for existing in meter_names:
                    if existing == item.meter_name:
                        found = True
                        break
                if not found:
                    meter_names.append(item.meter_name)
        
        if not meter_names:
            return []
        
        # Calculate aggregate score for each meter using logarithmic averaging
        scores = [0.0] * len(meter_names)
        for i, meter_name in enumerate(meter_names):
            score_sum = 0.0
            subtract = 0.0
            count = 0.0
            
            for item in results:
                if item.meter_name == meter_name:
                    if item.score == 0:
                        # Handle score == 0 case: add 1 before log, increment subtract
                        score_sum += math.log(item.score + 1)
                        count += 1.0
                        subtract += 1.0
                    else:
                        score_sum += math.log(item.score)
                        count += 1.0
            
            if count > 0:
                # Calculate aggregate: exp(sum(log(scores)) / count) - subtract
                scores[i] = math.exp(score_sum / count) - subtract
            else:
                scores[i] = float('inf')  # No scores, set to infinity
        
        # Sort scores and meter names together (maintain pairing)
        # Lower score is better for Levenshtein distance
        # Create parallel arrays like C# Array.Sort(scores, metes)
        paired = list(zip(scores, meter_names))
        paired.sort(key=lambda x: x[0])  # Sort by score (ascending)
        
        # Get the meter with best (lowest) score (first after sort, matching C# metes.First())
        final_meter = paired[0][1] if paired else ""
        
        if not final_meter:
            return []
        
        # Filter results: return only LineScansionResultFuzzy objects matching final_meter
        # Matching C# logic:
        # - If id == -2: match by meter name
        # - Else if meterIndex(finalMeter).Count > 0: match by id == Meters.id[meterIndex(finalMeter).First()]
        # - Special meters (id < -2) should also match by meter name
        filtered_results = []
        # Get meter indices for the final meter name (for regular meters)
        meter_indices = meter_index(final_meter)
        
        for item in results:
            if item.id == -2:
                # Rubai meter: match by meter name
                if item.meter_name == final_meter:
                    filtered_results.append(item)
            elif item.id < 0:
                # Special meter (id < -2): match by meter name
                if item.meter_name == final_meter:
                    filtered_results.append(item)
            elif meter_indices and len(meter_indices) > 0:
                # Regular or varied meter: match by meter ID using first index
                # In Python, id is the meter index itself, so check if it matches first index
                if item.id == meter_indices[0]:
                    filtered_results.append(item)
            else:
                # Fallback: if meter_index didn't find anything (e.g., varied meter),
                # match by meter name
                if item.meter_name == final_meter:
                    filtered_results.append(item)
        
        return filtered_results
