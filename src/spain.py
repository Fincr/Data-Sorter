"""Spain-specific postal code matching for Correos D1/D2 classification."""

from pathlib import Path
from typing import Optional

import yaml

from src.exceptions import ConfigError


def load_d1_mapping(config_path: Optional[Path] = None) -> dict[str, str]:
    """Load spain_d1.yaml and build a flat postal_code -> locality lookup dict.

    Returns:
        Dict mapping each D1 postal code (str) to its locality name.
        e.g. {"28001": "MADRID", "08001": "BARCELONA", ...}
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "spain_d1.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except FileNotFoundError:
        raise ConfigError(f"Spain D1 config not found: {config_path}")
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {config_path}: {e}")

    if not isinstance(data, dict) or "d1_localities" not in data:
        raise ConfigError("Spain D1 config must have a 'd1_localities' key")

    mapping: dict[str, str] = {}
    for entry in data["d1_localities"]:
        locality = entry["locality"]
        for code in entry["postal_codes"]:
            mapping[str(code)] = locality

    return mapping


def match_d1_postal_code(postcode: str, d1_mapping: dict[str, str]) -> Optional[str]:
    """Return locality name if postcode is in the D1 list, else None.

    Args:
        postcode: A 5-digit Spanish postal code string.
        d1_mapping: Dict from load_d1_mapping().

    Returns:
        Locality name (e.g. "MADRID") or None if not a D1 code.
    """
    return d1_mapping.get(postcode)
