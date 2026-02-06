"""Ireland-specific address classification — Dublin district matching."""

import re
from typing import Optional


# Dublin districts in the order they should be checked.
# Descending numeric order ensures "Dublin 18" is tested before "Dublin 1".
# "6W" is placed between 7 and 6 so it's tested before plain "6".
DUBLIN_DISTRICTS: list[str] = [
    "24", "22", "20", "18", "17", "16", "15", "14", "13",
    "12", "11", "10", "9", "8", "7", "6W", "6", "5", "4", "3", "2", "1",
]

# Pre-compiled patterns: dict mapping district label → compiled regex
_DISTRICT_PATTERNS: dict[str, re.Pattern] = {}


def build_dublin_patterns() -> dict[str, re.Pattern]:
    """Build and cache regex patterns for all Dublin districts.

    Strategy:
    - For multi-digit districts (10-24) and "6W": match "Dublin<sep><district>"
      where <sep> is optional whitespace/hyphen/dot. No lookahead needed because
      the multi-char suffix is unambiguous.
    - For single-digit districts (1-9, excluding 6 when 6W exists):
      match "Dublin<sep><digit>" followed by a negative lookahead that rejects
      another digit or 'W'/'w' (to avoid "Dublin 1" matching "Dublin 10" or
      "Dublin 6" matching "Dublin 6W").
      Also allow trailing suffixes like A-Z or punctuation (e.g. "Dublin 1A",
      "Dublin 1.").

    All patterns are case-insensitive.
    """
    global _DISTRICT_PATTERNS

    if _DISTRICT_PATTERNS:
        return _DISTRICT_PATTERNS

    patterns: dict[str, re.Pattern] = {}

    for district in DUBLIN_DISTRICTS:
        label = f"Dublin {district}"

        # Separator between "Dublin" and district: optional space/hyphen/dot, or none
        sep = r"[\s\-\.]*"

        if district == "6W":
            # "6W" — match Dublin + 6W, no lookahead needed (W is the disambiguator)
            regex = rf"dublin{sep}6\s*w(?![a-z])"
        elif len(district) >= 2 and district.isdigit():
            # Multi-digit (10-24): match exactly, reject trailing digit
            regex = rf"dublin{sep}{district}(?![0-9])"
        else:
            # Single digit (1-9, 6): reject trailing digit or W/w
            regex = rf"dublin{sep}{district}(?![0-9wW])"

        patterns[label] = re.compile(regex, re.IGNORECASE)

    _DISTRICT_PATTERNS = patterns
    return patterns


def match_dublin_district(text: str) -> Optional[str]:
    """Check if text contains a Dublin district reference.

    Returns the district label (e.g. "Dublin 10") or None.
    Districts are checked in descending order so longer matches take priority.
    """
    if not text:
        return None

    patterns = build_dublin_patterns()

    for label, pattern in patterns.items():
        if pattern.search(text):
            return label

    return None


def match_lettershop_keyword(text: str, keywords: list[dict]) -> Optional[str]:
    """Check text against lettershop area keywords from config.

    Args:
        text: Combined address string (already lowered by caller if needed).
        keywords: List of dicts with 'area' and 'patterns' keys from rules.yaml.

    Returns:
        Area name (e.g. "Blackrock") or None.
    """
    if not text:
        return None

    text_lower = text.lower()
    for entry in keywords:
        for pattern in entry["patterns"]:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return entry["area"]

    return None


def match_national_area(text: str, keywords: list[dict]) -> Optional[str]:
    """Check text against national area patterns from config.

    Args:
        text: Combined address string.
        keywords: List of dicts with 'area' and 'patterns' keys from rules.yaml.

    Returns:
        Area name (e.g. "Cork") or None.
    """
    if not text:
        return None

    for entry in keywords:
        for pattern in entry["patterns"]:
            if re.search(pattern, text, re.IGNORECASE):
                return entry["area"]

    return None


def match_eircode(text: str, eircode_routing: dict[str, str]) -> Optional[str]:
    """Check text for Eircode prefix and return the mapped area.

    Eircodes are 7 characters: 3-letter routing key + 4 alphanumeric chars.
    Example: D02 YX88 → "Dublin 2"
    """
    if not text:
        return None

    # Strip spaces and look for eircode-like patterns
    text_upper = text.upper().replace(" ", "")
    for prefix, area in eircode_routing.items():
        prefix_clean = prefix.upper().replace(" ", "")
        # Look for the prefix followed by 4 alphanumeric chars (full Eircode)
        pattern = rf"\b{re.escape(prefix_clean)}[A-Z0-9]{{4}}\b"
        if re.search(pattern, text_upper):
            return area

    # Also try matching just the prefix at a word boundary (partial Eircode)
    for prefix, area in eircode_routing.items():
        prefix_clean = prefix.upper().replace(" ", "")
        if prefix_clean in text_upper:
            return area

    return None
