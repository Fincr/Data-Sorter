"""Spain classifier — routes addresses to D1/D2 based on postal codes."""

import re
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import pandas as pd

from src.models import ClassificationResult, ColumnMapping
from src.spain import load_d1_mapping, match_d1_postal_code

# Regex to extract a 5-digit Spanish postal code
_POSTCODE_RE = re.compile(r"\b(\d{5})\b")


class SpainClassifier:
    """Postal-code-based classifier for Spanish addresses (Correos D1/D2)."""

    def __init__(self, config_path: Optional[Path] = None):
        self.d1_mapping = load_d1_mapping(config_path)

    def classify(
        self,
        df: pd.DataFrame,
        col_map: ColumnMapping,
        progress_callback: Callable[[int, int], None] | None = None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Classify all rows in the DataFrame.

        Returns:
            (df_classified, df_exceptions) — both with added columns:
            - Area
            - Routing
            - _exception_reason (exceptions only)
        """
        results: list[ClassificationResult] = []
        total = len(df)

        for i, (idx, row) in enumerate(df.iterrows()):
            result = self._classify_row(row, col_map)
            results.append(result)

            if progress_callback is not None:
                progress_callback(i + 1, total)

        df = df.copy()
        df["Area"] = [r.area for r in results]
        df["Routing"] = [r.routing for r in results]
        df["_exception_reason"] = [r.reason for r in results]

        # Split into classified and exceptions
        is_exception = df["_exception_reason"] != ""
        df_classified = df[~is_exception].drop(columns=["_exception_reason"])
        df_exceptions = df[is_exception].copy()

        # Sort classified: by Routing then Area alphabetically (D1 before D2)
        df_classified = df_classified.sort_values(
            by=["Routing", "Area"],
            kind="mergesort",
        )

        return df_classified, df_exceptions

    def _classify_row(
        self, row: pd.Series, col_map: ColumnMapping
    ) -> ClassificationResult:
        """Classify a single row by postal code lookup."""
        # 1. Try to get postcode from the mapped postcode column
        postcode = self._extract_postcode_from_column(row, col_map)

        # 2. If not found, try regex extraction from combined_address
        if not postcode:
            combined = str(row.get("combined_address", ""))
            postcode = self._extract_postcode_from_text(combined)

        # 3. No valid postcode → exception
        if not postcode:
            return ClassificationResult(
                area="", routing="", reason="No valid 5-digit postal code found"
            )

        # 4. Look up in D1 mapping
        locality = match_d1_postal_code(postcode, self.d1_mapping)
        if locality:
            return ClassificationResult(area=locality, routing="D1")

        # 5. Not in D1 → D2
        return ClassificationResult(area="D2", routing="D2")

    def _extract_postcode_from_column(
        self, row: pd.Series, col_map: ColumnMapping
    ) -> Optional[str]:
        """Try to extract a valid 5-digit postcode from the mapped postcode column."""
        if not col_map.postcode:
            return None

        raw = row.get(col_map.postcode)
        if pd.isna(raw):
            return None

        text = str(raw).strip()
        # CSV may read postal codes as integers, dropping leading zeros (e.g. 01001 → 1001).
        # Zero-pad purely numeric values back to 5 digits.
        if text.isdigit():
            text = text.zfill(5)
        match = _POSTCODE_RE.search(text)
        return match.group(1) if match else None

    def _extract_postcode_from_text(self, text: str) -> Optional[str]:
        """Try to extract a 5-digit postcode from free-text address."""
        if not text.strip():
            return None

        match = _POSTCODE_RE.search(text)
        return match.group(1) if match else None
