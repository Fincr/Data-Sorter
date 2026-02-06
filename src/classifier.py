"""Classification engine — loads YAML rules and applies them to addresses."""

import logging
import re
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from src.exceptions import ConfigError
from src.ireland import (
    match_dublin_district,
    match_eircode,
    match_lettershop_keyword,
    match_national_area,
)
from src.models import ClassificationResult, ColumnMapping

logger = logging.getLogger(__name__)


class Classifier:
    """Rule-based address classifier.

    Loads rules from YAML config at init. Classifies rows by:
    1. Detecting country (from country column or combined address scanning)
    2. Dispatching to country-specific handler
    3. Within handler: Eircode → Dublin district → lettershop keywords → national areas → fallback
    """

    def __init__(self, config_path: Optional[Path] = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "rules.yaml"

        self.config = self._load_config(config_path)
        self.country_handlers = {
            "ireland": self._classify_ireland,
        }
        self._compile_country_patterns()

    def _load_config(self, path: Path) -> dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except FileNotFoundError:
            raise ConfigError(f"Rules config not found: {path}")
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in {path}: {e}")

        if not isinstance(data, dict) or "countries" not in data:
            raise ConfigError("Rules config must have a 'countries' key")

        return data

    def _compile_country_patterns(self):
        """Pre-compile country detection regex patterns."""
        self._country_regexes: dict[str, list[re.Pattern]] = {}
        for country_name, country_cfg in self.config["countries"].items():
            patterns = country_cfg.get("country_patterns", [])
            self._country_regexes[country_name] = [
                re.compile(rf"\b{re.escape(p)}\b", re.IGNORECASE)
                for p in patterns
            ]

    def classify(
        self,
        df: pd.DataFrame,
        col_map: ColumnMapping,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Classify all rows in the DataFrame.

        Returns:
            (df_classified, df_exceptions) — both with added columns:
            - Lettershop Area
            - Routing
            - _exception_reason (exceptions only)
        """
        results: list[ClassificationResult] = []

        for idx, row in df.iterrows():
            combined = str(row.get("combined_address", ""))
            country_val = ""
            if col_map.country:
                raw = row.get(col_map.country)
                country_val = str(raw).strip() if pd.notna(raw) else ""

            result = self._classify_row(combined, country_val)
            results.append(result)

        df = df.copy()
        df["Lettershop Area"] = [r.area for r in results]
        df["Routing"] = [r.routing for r in results]
        df["_exception_reason"] = [r.reason for r in results]

        # Split into classified and exceptions
        is_exception = df["_exception_reason"] != ""
        df_classified = df[~is_exception].drop(columns=["_exception_reason"])
        df_exceptions = df[is_exception].copy()

        # Sort classified: LETTERSHOP first, then by area, preserving original order within groups
        df_classified = df_classified.sort_values(
            by=["Routing", "Lettershop Area"],
            key=lambda col: col.map(lambda x: (0 if x == "LETTERSHOP" else 1, x)),
            kind="mergesort",
        )

        return df_classified, df_exceptions

    def _classify_row(self, combined: str, country_val: str) -> ClassificationResult:
        """Classify a single row."""
        # Check for empty address
        if not combined.strip():
            return ClassificationResult(
                area="", routing="", reason="Empty address"
            )

        # Detect country
        country = self._detect_country(combined, country_val)

        if country and country in self.country_handlers:
            return self.country_handlers[country](combined)

        if country:
            # Known country but no handler
            return ClassificationResult(
                area=country.title(), routing="INTERNATIONAL", reason=""
            )

        # No country detected — try Ireland handler as default (since this is
        # primarily an Ireland tool). Only accept if a specific area matched
        # (not the generic "Ireland Other" fallback).
        ireland_result = self._classify_ireland(combined)
        if ireland_result.reason == "" and ireland_result.area != "Ireland Other":
            return ireland_result

        return ClassificationResult(
            area="", routing="", reason="Could not determine country or area"
        )

    def _detect_country(self, combined: str, country_val: str) -> Optional[str]:
        """Detect which country the address belongs to."""
        # Check country column first
        if country_val:
            for country_name, patterns in self._country_regexes.items():
                for pattern in patterns:
                    if pattern.search(country_val):
                        return country_name

        # Scan combined address
        for country_name, patterns in self._country_regexes.items():
            for pattern in patterns:
                if pattern.search(combined):
                    return country_name

        return None

    def _classify_ireland(self, combined: str) -> ClassificationResult:
        """Ireland-specific classification chain."""
        ireland_cfg = self.config["countries"]["ireland"]

        # 1. Check Eircode
        eircode_routing = ireland_cfg.get("eircode_routing", {})
        eircode_area = match_eircode(combined, eircode_routing)
        if eircode_area:
            routing = self._get_routing_for_area(eircode_area, ireland_cfg)
            return ClassificationResult(area=eircode_area, routing=routing)

        # 2. Check Dublin district
        dublin_district = match_dublin_district(combined)
        if dublin_district:
            return ClassificationResult(
                area=dublin_district, routing="LETTERSHOP"
            )

        # 3. Check lettershop keywords
        areas_cfg = ireland_cfg.get("areas", {})
        lettershop_kw = areas_cfg.get("lettershop_areas", {}).get("keywords", [])
        lettershop_area = match_lettershop_keyword(combined, lettershop_kw)
        if lettershop_area:
            return ClassificationResult(
                area=lettershop_area, routing="LETTERSHOP"
            )

        # 4. Check national areas
        national_kw = areas_cfg.get("national_areas", {}).get("keywords", [])
        national_area = match_national_area(combined, national_kw)
        if national_area:
            return ClassificationResult(
                area=national_area, routing="NATIONAL"
            )

        # 5. Fallback: Ireland Other
        fallback = areas_cfg.get("ireland_other", {})
        if fallback:
            return ClassificationResult(
                area=fallback.get("area", "Ireland Other"),
                routing=fallback.get("routing", "NATIONAL"),
            )

        return ClassificationResult(
            area="", routing="", reason="Ireland address: no area matched"
        )

    def _get_routing_for_area(self, area: str, country_cfg: dict) -> str:
        """Determine routing for a given area based on config."""
        # Check if area matches a Dublin district
        if area.startswith("Dublin "):
            return "LETTERSHOP"

        # Check lettershop areas
        areas_cfg = country_cfg.get("areas", {})
        lettershop_kw = areas_cfg.get("lettershop_areas", {}).get("keywords", [])
        for entry in lettershop_kw:
            if entry["area"] == area:
                return "LETTERSHOP"

        return "NATIONAL"
