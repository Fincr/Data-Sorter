"""Tests for src/config_editor.py — config load, validate, backup, save."""

import shutil
from pathlib import Path

import pytest
import yaml

from src.config_editor import (
    backup_config,
    load_columns_config,
    load_rules_config,
    save_columns_config,
    save_rules_config,
    validate_columns_config,
    validate_rules_config,
)

FIXTURES = Path(__file__).parent.parent / "config"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_rules() -> dict:
    """Return a minimal valid rules config."""
    return {
        "countries": {
            "ireland": {
                "country_patterns": ["ireland"],
                "eircode_routing": {"D01": "Dublin 1"},
                "areas": {
                    "dublin_districts": {
                        "routing": "LETTERSHOP",
                        "districts": [1],
                    },
                    "lettershop_areas": {
                        "routing": "LETTERSHOP",
                        "keywords": [
                            {"area": "Blackrock", "patterns": ["blackrock"]},
                        ],
                    },
                    "national_areas": {
                        "routing": "NATIONAL",
                        "keywords": [
                            {"area": "Cork", "patterns": ["\\bcork\\b"]},
                        ],
                    },
                    "ireland_other": {
                        "routing": "NATIONAL",
                        "area": "Ireland Other",
                    },
                },
            }
        }
    }


def _minimal_columns() -> dict:
    """Return a minimal valid columns config."""
    return {
        "address_line_1": ["address line 1", "address1"],
        "city": ["city", "town"],
    }


# ---------------------------------------------------------------------------
# validate_rules_config
# ---------------------------------------------------------------------------

class TestValidateRulesConfig:
    def test_valid_config(self):
        errors = validate_rules_config(_minimal_rules())
        assert errors == []

    def test_missing_countries_key(self):
        errors = validate_rules_config({"foo": "bar"})
        assert any("countries" in e for e in errors)

    def test_non_dict_input(self):
        errors = validate_rules_config("not a dict")
        assert any("dictionary" in e.lower() for e in errors)

    def test_empty_area_name_lettershop(self):
        data = _minimal_rules()
        data["countries"]["ireland"]["areas"]["lettershop_areas"]["keywords"].append(
            {"area": "", "patterns": ["test"]}
        )
        errors = validate_rules_config(data)
        assert any("empty" in e.lower() for e in errors)

    def test_empty_area_name_national(self):
        data = _minimal_rules()
        data["countries"]["ireland"]["areas"]["national_areas"]["keywords"].append(
            {"area": "", "patterns": ["test"]}
        )
        errors = validate_rules_config(data)
        assert any("empty" in e.lower() for e in errors)

    def test_duplicate_lettershop_areas(self):
        data = _minimal_rules()
        data["countries"]["ireland"]["areas"]["lettershop_areas"]["keywords"].append(
            {"area": "Blackrock", "patterns": ["blackrock2"]}
        )
        errors = validate_rules_config(data)
        assert any("duplicate" in e.lower() for e in errors)

    def test_duplicate_national_areas(self):
        data = _minimal_rules()
        data["countries"]["ireland"]["areas"]["national_areas"]["keywords"].append(
            {"area": "Cork", "patterns": ["cork2"]}
        )
        errors = validate_rules_config(data)
        assert any("duplicate" in e.lower() for e in errors)

    def test_invalid_eircode_prefix(self):
        data = _minimal_rules()
        data["countries"]["ireland"]["eircode_routing"]["AB"] = "Bad"
        errors = validate_rules_config(data)
        assert any("3 characters" in e for e in errors)

    def test_missing_patterns(self):
        data = _minimal_rules()
        data["countries"]["ireland"]["areas"]["lettershop_areas"]["keywords"].append(
            {"area": "NoPatterns", "patterns": []}
        )
        errors = validate_rules_config(data)
        assert any("at least one pattern" in e for e in errors)

    def test_real_config_file_is_valid(self):
        """The actual rules.yaml in the repo should pass validation."""
        data = load_rules_config(FIXTURES / "rules.yaml")
        errors = validate_rules_config(data)
        assert errors == [], f"Real config has errors: {errors}"


# ---------------------------------------------------------------------------
# validate_columns_config
# ---------------------------------------------------------------------------

class TestValidateColumnsConfig:
    def test_valid_config(self):
        errors = validate_columns_config(_minimal_columns())
        assert errors == []

    def test_non_dict_input(self):
        errors = validate_columns_config("not a dict")
        assert any("dictionary" in e.lower() for e in errors)

    def test_empty_alias_list(self):
        errors = validate_columns_config({"field": []})
        assert any("at least one" in e for e in errors)

    def test_empty_string_alias(self):
        errors = validate_columns_config({"field": ["good", ""]})
        assert any("empty alias" in e for e in errors)

    def test_non_list_value(self):
        errors = validate_columns_config({"field": "not a list"})
        assert any("list" in e.lower() for e in errors)

    def test_real_config_file_is_valid(self):
        """The actual columns.yaml in the repo should pass validation."""
        data = load_columns_config(FIXTURES / "columns.yaml")
        errors = validate_columns_config(data)
        assert errors == [], f"Real config has errors: {errors}"


# ---------------------------------------------------------------------------
# backup_config
# ---------------------------------------------------------------------------

class TestBackupConfig:
    def test_backup_creates_file(self, tmp_path):
        src = tmp_path / "test.yaml"
        src.write_text("key: value\n")
        backup_path = backup_config(src)
        assert backup_path.exists()
        assert backup_path.read_text() == "key: value\n"
        assert backup_path.suffix == ".bak"

    def test_backup_name_contains_timestamp(self, tmp_path):
        src = tmp_path / "test.yaml"
        src.write_text("key: value\n")
        backup_path = backup_config(src)
        # Should look like test.20260206_123456.bak
        assert backup_path.name.startswith("test.")
        assert backup_path.name.endswith(".bak")


# ---------------------------------------------------------------------------
# save_rules_config
# ---------------------------------------------------------------------------

class TestSaveRulesConfig:
    def test_save_creates_backup(self, tmp_path):
        path = tmp_path / "rules.yaml"
        original = _minimal_rules()
        # Write initial file
        with open(path, "w") as f:
            yaml.dump(original, f)

        _, errors = save_rules_config(path, original)
        assert errors == []
        # A .bak file should exist
        bak_files = list(tmp_path.glob("*.bak"))
        assert len(bak_files) == 1

    def test_save_with_validation_errors_does_not_write(self, tmp_path):
        path = tmp_path / "rules.yaml"
        original_content = "original: true\n"
        path.write_text(original_content)

        bad_data = {"no_countries": True}
        _, errors = save_rules_config(path, bad_data)
        assert len(errors) > 0
        # File should be unchanged
        assert path.read_text() == original_content
        # No backup should be created
        bak_files = list(tmp_path.glob("*.bak"))
        assert len(bak_files) == 0

    def test_round_trip_rules(self, tmp_path):
        """Load → save → load produces equivalent data."""
        # Copy real config to temp
        src = FIXTURES / "rules.yaml"
        dest = tmp_path / "rules.yaml"
        shutil.copy2(src, dest)

        data1 = load_rules_config(dest)
        save_rules_config(dest, data1)
        data2 = load_rules_config(dest)
        assert data1 == data2


# ---------------------------------------------------------------------------
# save_columns_config
# ---------------------------------------------------------------------------

class TestSaveColumnsConfig:
    def test_save_creates_backup(self, tmp_path):
        path = tmp_path / "columns.yaml"
        original = _minimal_columns()
        with open(path, "w") as f:
            yaml.dump(original, f)

        _, errors = save_columns_config(path, original)
        assert errors == []
        bak_files = list(tmp_path.glob("*.bak"))
        assert len(bak_files) == 1

    def test_save_with_validation_errors_does_not_write(self, tmp_path):
        path = tmp_path / "columns.yaml"
        original_content = "original: true\n"
        path.write_text(original_content)

        bad_data = {"field": []}
        _, errors = save_columns_config(path, bad_data)
        assert len(errors) > 0
        assert path.read_text() == original_content
        bak_files = list(tmp_path.glob("*.bak"))
        assert len(bak_files) == 0

    def test_round_trip_columns(self, tmp_path):
        """Load → save → load produces equivalent data."""
        src = FIXTURES / "columns.yaml"
        dest = tmp_path / "columns.yaml"
        shutil.copy2(src, dest)

        data1 = load_columns_config(dest)
        save_columns_config(dest, data1)
        data2 = load_columns_config(dest)
        assert data1 == data2
