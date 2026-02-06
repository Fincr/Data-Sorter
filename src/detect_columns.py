"""Auto-detect logical column mappings from messy spreadsheet headers."""

import difflib
from pathlib import Path
from typing import Optional

import yaml

from src.exceptions import ColumnDetectionError, ConfigError
from src.models import ColumnMapping

# Logical fields in priority order for matching
LOGICAL_FIELDS = [
    "address_line_1",
    "address_line_2",
    "address_line_3",
    "city",
    "county",
    "postcode",
    "country",
]

FUZZY_THRESHOLD = 0.75


def load_column_aliases(config_path: Path) -> dict[str, list[str]]:
    """Load column alias definitions from YAML config."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"Column config not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")

    if not isinstance(data, dict):
        raise ConfigError(f"Column config must be a mapping, got {type(data).__name__}")

    return data


def _normalize_simple(name: str) -> str:
    """Normalize a column name for comparison."""
    return " ".join(name.lower().strip().replace("_", " ").replace("-", " ").split())


def detect_columns(
    actual_columns: list[str],
    config_path: Optional[Path] = None,
) -> ColumnMapping:
    """Detect logical field → actual column mappings using three-pass matching.

    Each pass runs across ALL fields before moving to the next pass.
    This ensures exact matches are always preferred over fuzzy matches,
    even for lower-priority fields (e.g. "Country" exact-matches country
    before "county" can fuzzy-claim it).

    Pass 1: Exact match (case-insensitive, stripped)
    Pass 2: Normalized match (collapse spaces/underscores/hyphens)
    Pass 3: Fuzzy match (difflib.SequenceMatcher, threshold 75%)

    Within each pass, fields are matched in priority order.
    Once a column is claimed, it's unavailable for subsequent fields.
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "columns.yaml"

    aliases = load_column_aliases(config_path)
    available = set(actual_columns)
    mapping: dict[str, str] = {}

    # Pass 1: Exact match across all fields
    for field_name in LOGICAL_FIELDS:
        if field_name in mapping:
            continue
        field_aliases = aliases.get(field_name, [])
        matched = _exact_match(field_aliases, available)
        if matched is not None:
            mapping[field_name] = matched
            available.discard(matched)

    # Pass 2: Normalized match across all fields
    for field_name in LOGICAL_FIELDS:
        if field_name in mapping:
            continue
        field_aliases = aliases.get(field_name, [])
        matched = _normalized_match(field_aliases, available)
        if matched is not None:
            mapping[field_name] = matched
            available.discard(matched)

    # Pass 3: Fuzzy match across all fields
    for field_name in LOGICAL_FIELDS:
        if field_name in mapping:
            continue
        field_aliases = aliases.get(field_name, [])
        matched = _fuzzy_match(field_aliases, available)
        if matched is not None:
            mapping[field_name] = matched
            available.discard(matched)

    if not mapping:
        raise ColumnDetectionError(
            f"Could not detect any address columns. "
            f"Available columns: {actual_columns}"
        )

    return ColumnMapping(**mapping)


def _exact_match(aliases: list[str], available: set[str]) -> Optional[str]:
    """Pass 1: Exact case-insensitive match."""
    for alias in aliases:
        alias_lower = alias.lower().strip()
        for col in available:
            if col.lower().strip() == alias_lower:
                return col
    return None


def _normalized_match(aliases: list[str], available: set[str]) -> Optional[str]:
    """Pass 2: Normalized match (collapse whitespace/underscores/hyphens)."""
    for alias in aliases:
        alias_norm = _normalize_simple(alias)
        for col in available:
            if _normalize_simple(col) == alias_norm:
                return col
    return None


def _fuzzy_match(aliases: list[str], available: set[str]) -> Optional[str]:
    """Pass 3: Fuzzy match using SequenceMatcher."""
    best_score = 0.0
    best_col = None
    for alias in aliases:
        alias_norm = _normalize_simple(alias)
        for col in available:
            col_norm = _normalize_simple(col)
            score = difflib.SequenceMatcher(None, alias_norm, col_norm).ratio()
            if score > best_score and score >= FUZZY_THRESHOLD:
                best_score = score
                best_col = col
    return best_col
