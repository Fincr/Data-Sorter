"""Data models for the Data-Sorter pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ColumnMapping:
    """Maps logical field names to actual column names found in the input."""

    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    address_line_3: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None

    def mapped_columns(self) -> list[str]:
        """Return list of actual column names that were successfully mapped."""
        return [
            v
            for v in (
                self.address_line_1,
                self.address_line_2,
                self.address_line_3,
                self.city,
                self.county,
                self.postcode,
                self.country,
            )
            if v is not None
        ]

    def address_columns(self) -> list[str]:
        """Return mapped columns used for building the combined address (excludes country)."""
        return [
            v
            for v in (
                self.address_line_1,
                self.address_line_2,
                self.address_line_3,
                self.city,
                self.county,
                self.postcode,
            )
            if v is not None
        ]


@dataclass
class ClassificationResult:
    """Result of classifying a single row."""

    area: str  # e.g. "Dublin 10", "Cork", "LETTERSHOP"
    routing: str  # e.g. "LETTERSHOP", "NATIONAL"
    reason: str = ""  # explanation for exceptions


@dataclass
class PipelineStats:
    """Summary statistics from a classification run."""

    total_rows: int = 0
    classified_rows: int = 0
    exception_rows: int = 0
    area_counts: dict[str, int] = field(default_factory=dict)
    routing_counts: dict[str, int] = field(default_factory=dict)
