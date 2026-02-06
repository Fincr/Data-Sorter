"""Tests for the classification engine."""

import pandas as pd
import pytest
from pathlib import Path

from src.classifier import Classifier
from src.models import ColumnMapping

CONFIG_PATH = Path(__file__).parent.parent / "config" / "rules.yaml"


@pytest.fixture
def classifier():
    return Classifier(CONFIG_PATH)


def _make_df(addresses: list[str], countries: list[str] | None = None) -> pd.DataFrame:
    """Helper to create a test DataFrame with combined_address column."""
    data = {"combined_address": addresses}
    if countries is not None:
        data["Country"] = countries
    return pd.DataFrame(data)


class TestClassifier:
    def test_dublin_district(self, classifier):
        df = _make_df(["123 Main St, Dublin 10, Ireland"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, exceptions = classifier.classify(df, col_map)
        assert len(classified) == 1
        assert classified.iloc[0]["Lettershop Area"] == "Dublin 10"
        assert classified.iloc[0]["Routing"] == "LETTERSHOP"

    def test_dublin_1_not_dublin_10(self, classifier):
        """Dublin 10 should not be classified as Dublin 1."""
        df = _make_df(["Unit 5, Dublin 10"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Dublin 10"

    def test_dublin_6w(self, classifier):
        df = _make_df(["Rathgar, Dublin 6W"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Dublin 6W"

    def test_lettershop_keyword_blackrock(self, classifier):
        df = _make_df(["123 Main St, Blackrock, Co. Dublin"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Blackrock"
        assert classified.iloc[0]["Routing"] == "LETTERSHOP"

    def test_national_cork(self, classifier):
        df = _make_df(["456 Oak Road, Cork City"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Cork"
        assert classified.iloc[0]["Routing"] == "NATIONAL"

    def test_national_galway(self, classifier):
        df = _make_df(["12 Shop St, Galway"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Galway"
        assert classified.iloc[0]["Routing"] == "NATIONAL"

    def test_eircode_classification(self, classifier):
        df = _make_df(["123 Main St, D02 YX88"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Dublin 2"
        assert classified.iloc[0]["Routing"] == "LETTERSHOP"

    def test_empty_address_goes_to_exceptions(self, classifier):
        df = _make_df(["", "123 Main St, Dublin 1"], ["Ireland", "Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, exceptions = classifier.classify(df, col_map)
        assert len(exceptions) == 1
        assert "Empty address" in exceptions.iloc[0]["_exception_reason"]
        assert len(classified) == 1

    def test_no_country_column(self, classifier):
        """Should still classify if country is detected from address text."""
        df = _make_df(["123 Main St, Dublin 4, Ireland"])
        col_map = ColumnMapping()  # no country column
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Dublin 4"

    def test_ireland_other_fallback(self, classifier):
        """Address in Ireland but no specific area match → Ireland Other."""
        df = _make_df(["Some Random Place, Ireland"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Ireland Other"
        assert classified.iloc[0]["Routing"] == "NATIONAL"

    def test_unknown_address_goes_to_exceptions(self, classifier):
        """Address with no country or area match → exception."""
        df = _make_df(["12345 Unknown Place"])
        col_map = ColumnMapping()
        _, exceptions = classifier.classify(df, col_map)
        assert len(exceptions) == 1

    def test_sorting_lettershop_first(self, classifier):
        """LETTERSHOP rows should be sorted before NATIONAL rows."""
        df = _make_df(
            ["Main St, Cork, Ireland", "Unit 1, Dublin 4, Ireland", "Shop St, Galway, Ireland"],
            ["Ireland", "Ireland", "Ireland"],
        )
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        routings = classified["Routing"].tolist()
        assert routings[0] == "LETTERSHOP"
        # National after lettershop
        assert all(r == "NATIONAL" for r in routings[1:])

    def test_multiple_districts(self, classifier):
        """Multiple Dublin districts classified correctly."""
        df = _make_df(
            [
                "A, Dublin 1, Ireland",
                "B, Dublin 10, Ireland",
                "C, Dublin 6W, Ireland",
                "D, Dublin 24, Ireland",
            ],
            ["Ireland"] * 4,
        )
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        areas = classified["Lettershop Area"].tolist()
        assert "Dublin 1" in areas
        assert "Dublin 10" in areas
        assert "Dublin 6W" in areas
        assert "Dublin 24" in areas

    def test_co_prefix_county(self, classifier):
        """'Co. Kerry' should match Kerry."""
        df = _make_df(["Tralee, Co. Kerry"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Kerry"

    def test_swords_lettershop(self, classifier):
        df = _make_df(["Pavilions, Swords, Co Dublin"], ["Ireland"])
        col_map = ColumnMapping(country="Country")
        classified, _ = classifier.classify(df, col_map)
        assert classified.iloc[0]["Lettershop Area"] == "Swords"
        assert classified.iloc[0]["Routing"] == "LETTERSHOP"
