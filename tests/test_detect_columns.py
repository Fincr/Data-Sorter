"""Tests for column auto-detection."""

import pytest
from pathlib import Path

from src.detect_columns import detect_columns, _normalize_simple
from src.exceptions import ColumnDetectionError, ConfigError
from src.models import ColumnMapping

CONFIG_PATH = Path(__file__).parent.parent / "config" / "columns.yaml"


class TestDetectColumns:
    """Column detection integration tests using the real config."""

    def test_exact_match_standard_names(self):
        cols = ["Address Line 1", "Address Line 2", "City", "County", "Postcode", "Country"]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.address_line_1 == "Address Line 1"
        assert result.address_line_2 == "Address Line 2"
        assert result.city == "City"
        assert result.county == "County"
        assert result.postcode == "Postcode"
        assert result.country == "Country"

    def test_exact_match_case_insensitive(self):
        cols = ["address line 1", "CITY", "COUNTY", "postcode"]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.address_line_1 == "address line 1"
        assert result.city == "CITY"

    def test_normalized_match_underscores(self):
        cols = ["address_line_1", "address_line_2", "post_code"]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.address_line_1 == "address_line_1"
        assert result.address_line_2 == "address_line_2"

    def test_alias_match_street(self):
        """'Street' is an alias for address_line_1."""
        cols = ["Street", "Town", "Eircode", "Country"]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.address_line_1 == "Street"
        assert result.city == "Town"
        assert result.postcode == "Eircode"
        assert result.country == "Country"

    def test_fuzzy_match(self):
        """Slightly misspelled columns should still match via fuzzy."""
        cols = ["Addres Line 1", "Citty", "Countyy", "Postcod"]
        result = detect_columns(cols, CONFIG_PATH)
        # "Addres Line 1" is close enough to "address line 1"
        assert result.address_line_1 == "Addres Line 1"

    def test_mixed_real_world_columns(self):
        """Simulate a messy real-world spreadsheet."""
        cols = [
            "First Name", "Last Name", "Address1", "Address2",
            "Town/City", "County/State", "Zip Code", "Country Code",
            "Phone", "Email"
        ]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.address_line_1 == "Address1"
        assert result.address_line_2 == "Address2"
        assert result.city == "Town/City"
        assert result.county == "County/State"
        assert result.postcode == "Zip Code"
        assert result.country == "Country Code"

    def test_no_match_raises_error(self):
        cols = ["Name", "Phone", "Email", "ID"]
        with pytest.raises(ColumnDetectionError):
            detect_columns(cols, CONFIG_PATH)

    def test_partial_match_ok(self):
        """Even a single address column is sufficient (no error)."""
        cols = ["Name", "Address Line 1", "Phone"]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.address_line_1 == "Address Line 1"
        assert result.city is None

    def test_columns_not_double_claimed(self):
        """A column claimed by address_line_1 should not also be claimed by address_line_2."""
        cols = ["Address", "City", "Country"]
        result = detect_columns(cols, CONFIG_PATH)
        # "Address" is an alias for address_line_1 only
        assert result.address_line_1 == "Address"
        assert result.address_line_2 is None

    def test_address_columns_method(self):
        cols = ["Address Line 1", "City", "Postcode", "Country"]
        result = detect_columns(cols, CONFIG_PATH)
        assert result.country == "Country"
        addr_cols = result.address_columns()
        assert "Address Line 1" in addr_cols
        assert "City" in addr_cols
        assert "Postcode" in addr_cols
        assert "Country" not in addr_cols  # country excluded from address_columns

    def test_mapped_columns_method(self):
        cols = ["Address Line 1", "City", "Country"]
        result = detect_columns(cols, CONFIG_PATH)
        mapped = result.mapped_columns()
        assert "Address Line 1" in mapped
        assert "City" in mapped
        assert "Country" in mapped


class TestNormalize:
    def test_basic(self):
        assert _normalize_simple("Address Line 1") == "address line 1"

    def test_underscores(self):
        assert _normalize_simple("address_line_1") == "address line 1"

    def test_extra_spaces(self):
        assert _normalize_simple("  Address   Line  1  ") == "address line 1"

    def test_hyphens(self):
        assert _normalize_simple("address-line-1") == "address line 1"


class TestConfigErrors:
    def test_missing_config(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            detect_columns(["Address"], tmp_path / "nonexistent.yaml")

    def test_invalid_yaml(self, tmp_path):
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("{{invalid yaml")
        with pytest.raises(ConfigError, match="Invalid YAML"):
            detect_columns(["Address"], bad_file)
