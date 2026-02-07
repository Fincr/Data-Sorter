"""Tests for the Spain classifier — Province column and postal code sorting."""

import pandas as pd
import pytest
from unittest.mock import patch

from src.models import ColumnMapping
from src.spain_classifier import SpainClassifier


@pytest.fixture
def d1_mapping():
    """Minimal D1 mapping for testing — covers multiple provinces."""
    return {
        "28001": "MADRID",
        "28002": "MADRID",
        "08001": "BARCELONA",
        "08002": "BARCELONA",
        "01001": "VITORIA-GASTEIZ",
        "46001": "VALENCIA",
    }


@pytest.fixture
def col_map():
    return ColumnMapping(postcode="PostalCode")


@pytest.fixture
def classifier(d1_mapping):
    with patch.object(SpainClassifier, "__init__", lambda self, **kw: None):
        c = SpainClassifier()
        c.d1_mapping = d1_mapping
        return c


def _make_df(postcodes: list[str]) -> pd.DataFrame:
    return pd.DataFrame({
        "Name": [f"Row{i}" for i in range(len(postcodes))],
        "PostalCode": postcodes,
        "combined_address": [f"Calle {pc}" for pc in postcodes],
    })


class TestProvinceColumn:
    def test_province_present_in_classified(self, classifier, col_map):
        df = _make_df(["28001", "08001"])
        classified, _ = classifier.classify(df, col_map)
        assert "Province" in classified.columns

    def test_province_not_in_exceptions(self, classifier, col_map):
        df = _make_df(["XXXXX"])  # no valid postcode
        _, exceptions = classifier.classify(df, col_map)
        assert "Province" not in exceptions.columns

    def test_province_values(self, classifier, col_map):
        df = _make_df(["28001", "08001", "01001", "46001"])
        classified, _ = classifier.classify(df, col_map)
        provinces = dict(zip(classified["PostalCode"], classified["Province"]))
        assert provinces["28001"] == "28"
        assert provinces["08001"] == "08"
        assert provinces["01001"] == "01"
        assert provinces["46001"] == "46"


class TestPostalCodeSorting:
    def test_d1_sorted_by_postal_code(self, classifier, col_map):
        # Feed in reverse order — should come out sorted by postal code
        df = _make_df(["46001", "28002", "08001", "01001", "28001", "08002"])
        classified, _ = classifier.classify(df, col_map)
        postcodes = list(classified["PostalCode"])
        assert postcodes == ["01001", "08001", "08002", "28001", "28002", "46001"]

    def test_d2_sorted_by_postal_code(self, classifier, col_map):
        # Postal codes not in D1 → D2, should also be sorted by postal code
        df = _make_df(["50001", "30001", "10001"])
        classified, _ = classifier.classify(df, col_map)
        postcodes = list(classified["PostalCode"])
        assert postcodes == ["10001", "30001", "50001"]

    def test_d1_before_d2(self, classifier, col_map):
        # D1 routing sorts before D2 routing
        df = _make_df(["50001", "28001"])  # 50001=D2, 28001=D1
        classified, _ = classifier.classify(df, col_map)
        routings = list(classified["Routing"])
        assert routings == ["D1", "D2"]

    def test_mixed_routing_postal_order(self, classifier, col_map):
        # Multiple D1 and D2 — D1 group sorted by postcode, then D2 group sorted
        df = _make_df(["50001", "28001", "30001", "08001"])
        classified, _ = classifier.classify(df, col_map)
        result = list(zip(classified["Routing"], classified["PostalCode"]))
        assert result == [
            ("D1", "08001"),
            ("D1", "28001"),
            ("D2", "30001"),
            ("D2", "50001"),
        ]


class TestInternalColumnsCleanup:
    def test_no_postcode_internal_column(self, classifier, col_map):
        df = _make_df(["28001", "XXXXX"])
        classified, exceptions = classifier.classify(df, col_map)
        assert "_postcode" not in classified.columns
        assert "_postcode" not in exceptions.columns
