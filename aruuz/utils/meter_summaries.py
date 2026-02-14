"""
Meter summaries for Urdu poetry meters.

Derived from aruuz.meters._METERS_DATA. Each entry includes the Roman name
and a short English description. Only unique meter names (by Urdu name) are included.
"""

from typing import Dict, Any

from aruuz.meters import _METERS_DATA

# Roman modifier terms → summary fragment (for "where ..." clause)
_STRUCTURE = {
    "Musamman": "eight-foot",
    "Musaddas": "six-foot",
    "Murabbaʿ": "four-foot",
}


def _summary_from_roman(roman: str) -> str:
    """Build a short English summary from the Roman meter name."""
    parts = roman.split()
    if not parts:
        return "A classical Arabic meter."
    bahr = parts[0]  # e.g. Hazaj, Muḍāriʿ, Rajaz

    structure = "meter"
    for token, desc in _STRUCTURE.items():
        if token in roman:
            structure = f"{desc} form"
            break

    modifiers = []
    if "Sālim" in roman and "Makhbūn" not in roman and "Akhrab" not in roman and "Makfūf" not in roman:
        return f"An unmodified {structure} of Bahr {bahr}."
    if "Akhrab" in roman:
        modifiers.append("the first foot is altered")
    if "Makfūf" in roman:
        modifiers.append("the end is modified")
    if "Maḥdhūf" in roman:
        modifiers.append("the final part is truncated")
    if "Maqṭūʿ" in roman:
        modifiers.append("the final foot is shortened")
    if "Maqṭūf" in roman:
        modifiers.append("the final part is removed")
    if "Maqbūz" in roman:
        modifiers.append("a long element is contracted")
    if "Maṭwī" in roman:
        modifiers.append("the foot is folded (contracted)")
    if "Muḍāʿaf" in roman:
        modifiers.append("the pattern is doubled")
    if "Makhbūn" in roman:
        modifiers.append("a foot is altered (concealed)")
    if "Mashkūl" in roman:
        modifiers.append("a foot appears in altered form")
    if "Maksūf" in roman:
        modifiers.append("a letter or sound is removed")
    if "Manḥūr" in roman:
        modifiers.append("the pattern is transformed")
    if "Makhlaʿ" in roman:
        modifiers.append("a foot is disjointed or altered")
    if "Athram" in roman:
        modifiers.append("the first sound of a foot is dropped")
    if "Athlam" in roman:
        modifiers.append("the beginning is shortened")
    if "Ashtar" in roman:
        modifiers.append("the meter has a zihaf (deviation)")
    if "Akhram" in roman:
        modifiers.append("the first foot is altered")
    if "Muskann" in roman:
        modifiers.append("the foot or line ends with sukūn")
    if "Maḥjūf" in roman:
        modifiers.append("part of the meter is curtailed")

    article = "An" if structure.startswith(("eight", "eight-foot")) else "A"
    if not modifiers:
        return f"{article} {structure} of Bahr {bahr}."
    if len(modifiers) == 1:
        return f"{article} {structure} of Bahr {bahr} where {modifiers[0]}."
    return f"{article} {structure} of Bahr {bahr} where {', '.join(modifiers[:-1])}, and {modifiers[-1]}."


def _build_meter_summaries() -> Dict[str, Dict[str, Any]]:
    """Build METER_SUMMARIES from _METERS_DATA with unique meter names only."""
    seen: set = set()
    out: Dict[str, Dict[str, Any]] = {}
    for m in _METERS_DATA:
        if m.name in seen:
            continue
        seen.add(m.name)
        out[m.name] = {
            "roman": m.roman,
            "summary": _summary_from_roman(m.roman),
        }
    return out


METER_SUMMARIES: Dict[str, Dict[str, str]] = _build_meter_summaries()
