"""Tests for combined address building."""

import pandas as pd
import pytest

from src.build_address import add_combined_address
from src.models import ColumnMapping


class TestAddCombinedAddress:
    def test_basic_concatenation(self):
        df = pd.DataFrame({
            "Addr1": ["123 Main St"],
            "City": ["Dublin"],
            "Postcode": ["D01 AB12"],
        })
        col_map = ColumnMapping(address_line_1="Addr1", city="City", postcode="Postcode")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == "123 Main St, Dublin, D01 AB12"

    def test_skips_nan(self):
        df = pd.DataFrame({
            "Addr1": ["123 Main St"],
            "Addr2": [None],
            "City": ["Dublin"],
        })
        col_map = ColumnMapping(address_line_1="Addr1", address_line_2="Addr2", city="City")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == "123 Main St, Dublin"

    def test_skips_empty_string(self):
        df = pd.DataFrame({
            "Addr1": ["123 Main St"],
            "Addr2": [""],
            "City": ["Dublin"],
        })
        col_map = ColumnMapping(address_line_1="Addr1", address_line_2="Addr2", city="City")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == "123 Main St, Dublin"

    def test_all_nan_produces_empty(self):
        df = pd.DataFrame({
            "Addr1": [None],
            "City": [None],
        })
        col_map = ColumnMapping(address_line_1="Addr1", city="City")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == ""

    def test_strips_whitespace(self):
        df = pd.DataFrame({
            "Addr1": ["  123 Main St  "],
            "City": [" Dublin "],
        })
        col_map = ColumnMapping(address_line_1="Addr1", city="City")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == "123 Main St, Dublin"

    def test_no_address_columns(self):
        """If no address columns are mapped, combined_address is empty."""
        df = pd.DataFrame({"Name": ["Alice"]})
        col_map = ColumnMapping()
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == ""

    def test_does_not_mutate_original(self):
        df = pd.DataFrame({"Addr1": ["123 Main St"]})
        col_map = ColumnMapping(address_line_1="Addr1")
        result = add_combined_address(df, col_map)
        assert "combined_address" in result.columns
        assert "combined_address" not in df.columns

    def test_multiple_rows(self):
        df = pd.DataFrame({
            "Addr1": ["123 Main St", "456 Oak Ave", "789 Elm Rd"],
            "City": ["Dublin", "Cork", "Galway"],
        })
        col_map = ColumnMapping(address_line_1="Addr1", city="City")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == "123 Main St, Dublin"
        assert result["combined_address"].iloc[1] == "456 Oak Ave, Cork"
        assert result["combined_address"].iloc[2] == "789 Elm Rd, Galway"

    def test_country_excluded_from_address(self):
        """Country column should NOT be included in combined_address."""
        df = pd.DataFrame({
            "Addr1": ["123 Main St"],
            "City": ["Dublin"],
            "Country": ["Ireland"],
        })
        col_map = ColumnMapping(address_line_1="Addr1", city="City", country="Country")
        result = add_combined_address(df, col_map)
        assert "Ireland" not in result["combined_address"].iloc[0]
        assert result["combined_address"].iloc[0] == "123 Main St, Dublin"

    def test_numeric_values_converted(self):
        """Numeric values in address columns should be converted to string."""
        df = pd.DataFrame({
            "Addr1": [123],
            "City": ["Dublin"],
        })
        col_map = ColumnMapping(address_line_1="Addr1", city="City")
        result = add_combined_address(df, col_map)
        assert result["combined_address"].iloc[0] == "123, Dublin"
