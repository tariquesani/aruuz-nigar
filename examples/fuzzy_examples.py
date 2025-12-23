"""
Examples demonstrating fuzzy matching for imperfect/experimental Urdu poetry.

Fuzzy matching allows the scansion engine to identify meters even when poetry
doesn't perfectly match traditional meter patterns. This is useful for:
- Experimental poetry
- Imperfect meter usage
- Poetry with minor deviations from standard patterns
- Educational purposes to see close matches

The fuzzy matching uses Levenshtein distance to find the closest matching
meter patterns, with lower scores indicating better matches.
"""

from aruuz.scansion import Scansion
from aruuz.models import Lines


def example_1_single_line_fuzzy():
    """
    Example 1: Using scan_line_fuzzy() for a single line.
    
    This demonstrates how to scan a single line with fuzzy matching
    to find the closest matching meter patterns.
    """
    print("=" * 70)
    print("Example 1: Single Line Fuzzy Matching")
    print("=" * 70)
    
    # Create a scansion instance
    scansion = Scansion()
    
    # Create a line with imperfect meter (slightly deviates from perfect pattern)
    # This line might not match perfectly in regular mode
    line_text = "دل کی بات کہیں تو کہہ دیں"
    line = Lines(line_text)
    
    print(f"\nLine: {line_text}")
    print("\nScanning with fuzzy matching...\n")
    
    # Use scan_line_fuzzy() to get fuzzy results
    results = scansion.scan_line_fuzzy(line, 0)
    
    if results:
        print(f"Found {len(results)} possible meter matches:\n")
        for i, result in enumerate(results[:5], 1):  # Show top 5 matches
            print(f"Match {i}:")
            print(f"  Meter: {result.meter_name}")
            print(f"  Score: {result.score} (lower is better)")
            print(f"  Feet: {result.feet}")
            print(f"  Code: {''.join(result.word_taqti)}")
            print()
    else:
        print("No matches found.")
    
    print()


def example_2_multiple_lines_fuzzy():
    """
    Example 2: Using scan_lines_fuzzy() for a complete poem.
    
    This demonstrates how to scan multiple lines and get consolidated
    results showing the best matching meter across all lines.
    """
    print("=" * 70)
    print("Example 2: Multiple Lines Fuzzy Matching")
    print("=" * 70)
    
    # Create a scansion instance
    scansion = Scansion()
    
    # Add multiple lines of poetry (some with imperfect meter)
    lines = [
        "دل کی بات کہیں تو کہہ دیں",
        "یہ بھی ایک بات ہے کہ کیا کہیں",
        "زندگی کا سفر ہے یہ مشکل",
        "راستے میں ملے ہیں کتنے لوگ"
    ]
    
    print("\nPoem lines:")
    for i, line_text in enumerate(lines, 1):
        print(f"  {i}. {line_text}")
        scansion.add_line(Lines(line_text))
    
    print("\nScanning all lines with fuzzy matching...\n")
    
    # Use scan_lines_fuzzy() to get consolidated results
    results = scansion.scan_lines_fuzzy()
    
    if results:
        print(f"Found {len(results)} results (consolidated to best meter):\n")
        for i, result in enumerate(results, 1):
            print(f"Line {i}: {result.original_line}")
            print(f"  Meter: {result.meter_name}")
            print(f"  Score: {result.score}")
            print(f"  Feet: {result.feet}")
            print()
    else:
        print("No matches found.")
    
    print()


def example_3_fuzzy_mode_flag():
    """
    Example 3: Using fuzzy mode via scansion.fuzzy = True.
    
    This demonstrates the simpler approach of setting the fuzzy flag
    and using the regular scan_lines() method, which will automatically
    use fuzzy matching when fuzzy=True.
    """
    print("=" * 70)
    print("Example 3: Fuzzy Mode via Flag")
    print("=" * 70)
    
    # Create a scansion instance
    scansion = Scansion()
    
    # Enable fuzzy mode
    scansion.fuzzy = True
    
    # Add lines with experimental/imperfect meter
    lines = [
        "تجھے دیکھا تو یہ خیال آیا",
        "زندگی کیا ہے ایک سفر ہے",
        "دل میں ہے درد تو کیا کریں"
    ]
    
    print("\nPoem lines:")
    for line_text in lines:
        print(f"  {line_text}")
        scansion.add_line(Lines(line_text))
    
    print("\nScanning with fuzzy mode enabled...\n")
    
    # Use regular scan_lines() - it will use fuzzy path when fuzzy=True
    results = scansion.scan_lines()
    
    if results:
        print(f"Found {len(results)} results:\n")
        for i, result in enumerate(results, 1):
            print(f"Line {i}: {result.original_line}")
            if hasattr(result, 'meter_name'):
                print(f"  Meter: {result.meter_name}")
            if hasattr(result, 'score'):
                print(f"  Score: {result.score}")
            if hasattr(result, 'feet'):
                print(f"  Feet: {result.feet}")
            print()
    else:
        print("No matches found.")
    
    print()


def example_4_imperfect_poetry():
    """
    Example 4: Experimental/Imperfect Poetry Examples.
    
    This demonstrates fuzzy matching with poetry that intentionally
    deviates from traditional meter patterns or has experimental forms.
    """
    print("=" * 70)
    print("Example 4: Imperfect/Experimental Poetry")
    print("=" * 70)
    
    scansion = Scansion()
    
    # Example of poetry with intentional meter variations
    experimental_lines = [
        "آج کا دن بھی گزر گیا",  # Slightly irregular
        "کل کیا ہوگا کون جانتا ہے",  # Experimental length
        "زندگی ہے یہ ایک کہانی",  # Close but not perfect
    ]
    
    print("\nExperimental poetry lines:")
    for line_text in experimental_lines:
        print(f"  {line_text}")
        scansion.add_line(Lines(line_text))
    
    print("\nScanning with fuzzy matching...\n")
    
    # Get fuzzy results
    results = scansion.scan_lines_fuzzy()
    
    if results:
        print("Best matches found:\n")
        for i, result in enumerate(results, 1):
            print(f"Line: {result.original_line}")
            print(f"  Best Match: {result.meter_name}")
            print(f"  Match Score: {result.score} (lower = better match)")
            print(f"  Meter Pattern: {result.feet}")
            print(f"  Word Codes: {' | '.join(result.word_taqti)}")
            print()
            
            # Show score interpretation
            if result.score == 0:
                print("  → Perfect match!")
            elif result.score <= 2:
                print("  → Very close match (minor deviation)")
            elif result.score <= 5:
                print("  → Close match (some deviation)")
            else:
                print("  → Approximate match (significant deviation)")
            print()
    else:
        print("No matches found.")
    
    print()


def example_5_comparing_fuzzy_vs_regular():
    """
    Example 5: Comparing Fuzzy vs Regular Matching.
    
    This demonstrates the difference between regular scansion (which requires
    perfect matches) and fuzzy scansion (which finds closest matches).
    """
    print("=" * 70)
    print("Example 5: Fuzzy vs Regular Matching Comparison")
    print("=" * 70)
    
    # Line that might not match perfectly
    line_text = "دل کی بات کہیں تو کہہ دیں"
    line = Lines(line_text)
    
    print(f"\nLine: {line_text}\n")
    
    # Regular matching (fuzzy=False)
    print("1. Regular Matching (fuzzy=False):")
    print("-" * 50)
    scansion_regular = Scansion()
    scansion_regular.fuzzy = False
    scansion_regular.add_line(line)
    results_regular = scansion_regular.scan_lines()
    
    if results_regular:
        print(f"   Found {len(results_regular)} perfect match(es)")
        for result in results_regular[:3]:
            if hasattr(result, 'meter_name'):
                print(f"   Meter: {result.meter_name}")
    else:
        print("   No perfect matches found")
    
    print()
    
    # Fuzzy matching (fuzzy=True)
    print("2. Fuzzy Matching (fuzzy=True):")
    print("-" * 50)
    scansion_fuzzy = Scansion()
    scansion_fuzzy.fuzzy = True
    scansion_fuzzy.add_line(line)
    results_fuzzy = scansion_fuzzy.scan_lines()
    
    if results_fuzzy:
        print(f"   Found {len(results_fuzzy)} closest match(es)")
        for result in results_fuzzy[:3]:
            if hasattr(result, 'meter_name'):
                print(f"   Meter: {result.meter_name}")
            if hasattr(result, 'score'):
                print(f"   Score: {result.score} (lower is better)")
    else:
        print("   No matches found")
    
    print()
    
    # Direct fuzzy method
    print("3. Using scan_line_fuzzy() directly:")
    print("-" * 50)
    scansion_direct = Scansion()
    results_direct = scansion_direct.scan_line_fuzzy(line, 0)
    
    if results_direct:
        print(f"   Found {len(results_direct)} possible match(es)")
        # Sort by score to show best matches first
        sorted_results = sorted(results_direct, key=lambda x: x.score)
        for result in sorted_results[:3]:
            print(f"   Meter: {result.meter_name}")
            print(f"   Score: {result.score}")
    else:
        print("   No matches found")
    
    print()


def example_6_score_interpretation():
    """
    Example 6: Understanding Fuzzy Scores.
    
    This demonstrates how to interpret fuzzy matching scores and
    understand what they mean in terms of meter matching quality.
    """
    print("=" * 70)
    print("Example 6: Understanding Fuzzy Scores")
    print("=" * 70)
    
    scansion = Scansion()
    
    # Different lines with varying degrees of meter deviation
    test_cases = [
        ("نقش فریادی ہے کس کی شوخیِ تحریر کا", "Well-known perfect line"),
        ("دل کی بات کہیں تو کہہ دیں", "Slightly imperfect"),
        ("زندگی کا سفر ہے یہ مشکل بہت", "More deviation"),
    ]
    
    print("\nTesting different lines:\n")
    
    for line_text, description in test_cases:
        print(f"Line: {line_text}")
        print(f"Description: {description}")
        
        line = Lines(line_text)
        results = scansion.scan_line_fuzzy(line, 0)
        
        if results:
            # Get best match (lowest score)
            best_match = min(results, key=lambda x: x.score)
            print(f"  Best Match: {best_match.meter_name}")
            print(f"  Score: {best_match.score}")
            
            # Interpret score
            if best_match.score == 0:
                print("  → Perfect match! No deviations detected.")
            elif best_match.score == 1:
                print("  → Excellent match! Only 1 character difference.")
            elif best_match.score <= 3:
                print("  → Good match! Minor deviations (2-3 characters).")
            elif best_match.score <= 6:
                print("  → Acceptable match! Some deviations (4-6 characters).")
            else:
                print("  → Approximate match! Significant deviations (>6 characters).")
        else:
            print("  → No matches found.")
        
        print()
    
    print("\nNote: Score represents Levenshtein distance - the number of")
    print("character changes needed to match the meter pattern exactly.")
    print("Lower scores indicate better matches.")
    print()


def main():
    """
    Run all fuzzy matching examples.
    """
    print("\n" + "=" * 70)
    print("Fuzzy Matching Examples for Urdu Poetry Scansion")
    print("=" * 70)
    print("\nThese examples demonstrate how to use fuzzy matching to identify")
    print("meters in imperfect or experimental Urdu poetry.\n")
    
    try:
        example_1_single_line_fuzzy()
        example_2_multiple_lines_fuzzy()
        example_3_fuzzy_mode_flag()
        example_4_imperfect_poetry()
        example_5_comparing_fuzzy_vs_regular()
        example_6_score_interpretation()
        
        print("=" * 70)
        print("All examples completed!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("This might be due to database connectivity or other setup issues.")
        print("Fuzzy matching should still work, but may have limited functionality.")


if __name__ == "__main__":
    main()

