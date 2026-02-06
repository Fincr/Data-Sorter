"""Config editor backend — load, validate, backup, and save YAML config files."""

import shutil
from datetime import datetime
from pathlib import Path

import yaml


def load_rules_config(path: Path) -> dict:
    """Load and parse rules.yaml."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    return data


def load_columns_config(path: Path) -> dict:
    """Load and parse columns.yaml."""
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if data is None:
        return {}
    return data


def validate_rules_config(data: dict) -> list[str]:
    """Validate rules config structure. Returns list of error strings (empty = valid)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Config must be a dictionary"]

    if "countries" not in data:
        errors.append("Missing required 'countries' key")
        return errors

    countries = data["countries"]
    if not isinstance(countries, dict):
        errors.append("'countries' must be a dictionary")
        return errors

    for country_name, country_cfg in countries.items():
        if not isinstance(country_cfg, dict):
            errors.append(f"Country '{country_name}' must be a dictionary")
            continue

        # Validate eircode routing
        eircode_routing = country_cfg.get("eircode_routing", {})
        if isinstance(eircode_routing, dict):
            for prefix in eircode_routing:
                if len(str(prefix)) != 3:
                    errors.append(
                        f"Eircode prefix '{prefix}' must be exactly 3 characters"
                    )

        # Validate areas
        areas = country_cfg.get("areas", {})
        if not isinstance(areas, dict):
            continue

        # Validate lettershop areas
        lettershop = areas.get("lettershop_areas", {})
        if isinstance(lettershop, dict):
            keywords = lettershop.get("keywords", [])
            if isinstance(keywords, list):
                seen_areas: set[str] = set()
                for entry in keywords:
                    if not isinstance(entry, dict):
                        errors.append("Each lettershop keyword entry must be a dictionary")
                        continue
                    area = entry.get("area", "")
                    if not area or not str(area).strip():
                        errors.append("Lettershop area name must not be empty")
                    else:
                        if area in seen_areas:
                            errors.append(f"Duplicate lettershop area: '{area}'")
                        seen_areas.add(area)
                    patterns = entry.get("patterns", [])
                    if not patterns:
                        errors.append(
                            f"Lettershop area '{area}' must have at least one pattern"
                        )

        # Validate national areas
        national = areas.get("national_areas", {})
        if isinstance(national, dict):
            keywords = national.get("keywords", [])
            if isinstance(keywords, list):
                seen_areas = set()
                for entry in keywords:
                    if not isinstance(entry, dict):
                        errors.append("Each national keyword entry must be a dictionary")
                        continue
                    area = entry.get("area", "")
                    if not area or not str(area).strip():
                        errors.append("National area name must not be empty")
                    else:
                        if area in seen_areas:
                            errors.append(f"Duplicate national area: '{area}'")
                        seen_areas.add(area)
                    patterns = entry.get("patterns", [])
                    if not patterns:
                        errors.append(
                            f"National area '{area}' must have at least one pattern"
                        )

    return errors


def validate_columns_config(data: dict) -> list[str]:
    """Validate columns config structure. Returns list of error strings (empty = valid)."""
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Config must be a dictionary"]

    for field, aliases in data.items():
        if not isinstance(aliases, list):
            errors.append(f"Field '{field}' must map to a list of aliases")
            continue
        if not aliases:
            errors.append(f"Field '{field}' must have at least one alias")
            continue
        for i, alias in enumerate(aliases):
            if not isinstance(alias, str) or not alias.strip():
                errors.append(f"Field '{field}' has an empty alias at position {i + 1}")

    return errors


def backup_config(path: Path) -> Path:
    """Create a timestamped backup of a config file. Returns the backup path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = path.with_suffix(f".{timestamp}.bak")
    shutil.copy2(path, backup_path)
    return backup_path


def save_rules_config(path: Path, data: dict) -> tuple[Path, list[str]]:
    """Validate, backup, and save rules config.

    Returns:
        (backup_path, errors) — errors is empty on success.
        If validation fails, the file is NOT written and backup_path is empty.
    """
    errors = validate_rules_config(data)
    if errors:
        return Path(), errors

    backup_path = backup_config(path)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return backup_path, []


def save_columns_config(path: Path, data: dict) -> tuple[Path, list[str]]:
    """Validate, backup, and save columns config.

    Returns:
        (backup_path, errors) — errors is empty on success.
        If validation fails, the file is NOT written and backup_path is empty.
    """
    errors = validate_columns_config(data)
    if errors:
        return Path(), errors

    backup_path = backup_config(path)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    return backup_path, []
