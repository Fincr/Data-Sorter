"""Tests for Dublin district matching — 30+ parameterized edge cases."""

import pytest

from src.ireland import (
    build_dublin_patterns,
    match_dublin_district,
    match_eircode,
    match_lettershop_keyword,
    match_national_area,
)


class TestMatchDublinDistrict:
    """Core Dublin district matching tests."""

    # --- Standard formats ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Dublin 1", "Dublin 1"),
            ("Dublin 2", "Dublin 2"),
            ("Dublin 3", "Dublin 3"),
            ("Dublin 4", "Dublin 4"),
            ("Dublin 5", "Dublin 5"),
            ("Dublin 6", "Dublin 6"),
            ("Dublin 7", "Dublin 7"),
            ("Dublin 8", "Dublin 8"),
            ("Dublin 9", "Dublin 9"),
            ("Dublin 10", "Dublin 10"),
            ("Dublin 11", "Dublin 11"),
            ("Dublin 12", "Dublin 12"),
            ("Dublin 13", "Dublin 13"),
            ("Dublin 14", "Dublin 14"),
            ("Dublin 15", "Dublin 15"),
            ("Dublin 16", "Dublin 16"),
            ("Dublin 17", "Dublin 17"),
            ("Dublin 18", "Dublin 18"),
            ("Dublin 20", "Dublin 20"),
            ("Dublin 22", "Dublin 22"),
            ("Dublin 24", "Dublin 24"),
        ],
        ids=lambda v: str(v),
    )
    def test_standard_district_formats(self, text, expected):
        assert match_dublin_district(text) == expected

    # --- Critical: Dublin 1 must NOT match Dublin 10-18 ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Dublin 10", "Dublin 10"),
            ("Dublin 11", "Dublin 11"),
            ("Dublin 12", "Dublin 12"),
            ("Dublin 13", "Dublin 13"),
            ("Dublin 14", "Dublin 14"),
            ("Dublin 15", "Dublin 15"),
            ("Dublin 16", "Dublin 16"),
            ("Dublin 17", "Dublin 17"),
            ("Dublin 18", "Dublin 18"),
        ],
    )
    def test_dublin_1_does_not_match_teens(self, text, expected):
        """Dublin 10-18 must match their own district, not Dublin 1."""
        result = match_dublin_district(text)
        assert result == expected
        assert result != "Dublin 1"

    # --- Dublin 6W special case ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Dublin 6W", "Dublin 6W"),
            ("dublin 6w", "Dublin 6W"),
            ("Dublin6W", "Dublin 6W"),
            ("Dublin 6w", "Dublin 6W"),
            ("DUBLIN 6W", "Dublin 6W"),
        ],
    )
    def test_dublin_6w(self, text, expected):
        assert match_dublin_district(text) == expected

    def test_dublin_6_does_not_match_6w(self):
        """Dublin 6W must match 6W, not plain Dublin 6."""
        result = match_dublin_district("Dublin 6W")
        assert result == "Dublin 6W"
        assert result != "Dublin 6"

    def test_dublin_6_plain(self):
        """Plain Dublin 6 (no W) should match Dublin 6."""
        assert match_dublin_district("Dublin 6") == "Dublin 6"

    # --- No separator / compact formats ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Dublin1", "Dublin 1"),
            ("Dublin10", "Dublin 10"),
            ("Dublin24", "Dublin 24"),
            ("Dublin6W", "Dublin 6W"),
            ("dublin1", "Dublin 1"),
            ("DUBLIN10", "Dublin 10"),
        ],
    )
    def test_no_separator(self, text, expected):
        assert match_dublin_district(text) == expected

    # --- Case insensitivity ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("dublin 1", "Dublin 1"),
            ("DUBLIN 1", "Dublin 1"),
            ("Dublin 1", "Dublin 1"),
            ("dUBLIN 10", "Dublin 10"),
        ],
    )
    def test_case_insensitive(self, text, expected):
        assert match_dublin_district(text) == expected

    # --- Embedded in longer addresses ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("123 Main St, Dublin 1, Ireland", "Dublin 1"),
            ("Apt 4, Block B, Dublin 10", "Dublin 10"),
            ("Dublin 6W, Rathgar", "Dublin 6W"),
            ("Co. Dublin, Dublin 15, D15 ABC1", "Dublin 15"),
            ("Unit 5, Some Place, Dublin 24, Ireland", "Dublin 24"),
        ],
    )
    def test_embedded_in_address(self, text, expected):
        assert match_dublin_district(text) == expected

    # --- Separator variants ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Dublin-1", "Dublin 1"),
            ("Dublin.1", "Dublin 1"),
            ("Dublin - 10", "Dublin 10"),
            ("Dublin.10", "Dublin 10"),
        ],
    )
    def test_separator_variants(self, text, expected):
        assert match_dublin_district(text) == expected

    # --- No match cases ---

    @pytest.mark.parametrize(
        "text",
        [
            "",
            "Cork",
            "Dublin",  # no district number
            "Dublin, Ireland",
            "123 Main Street, Galway",
            "Co. Dublin",
        ],
    )
    def test_no_match(self, text):
        assert match_dublin_district(text) is None

    # --- None / empty ---

    def test_none_input(self):
        assert match_dublin_district(None) is None

    def test_empty_string(self):
        assert match_dublin_district("") is None

    # --- Dublin 2 should not match Dublin 20/22/24 ---

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("Dublin 20", "Dublin 20"),
            ("Dublin 22", "Dublin 22"),
            ("Dublin 24", "Dublin 24"),
        ],
    )
    def test_dublin_2_does_not_match_twenties(self, text, expected):
        result = match_dublin_district(text)
        assert result == expected
        assert result != "Dublin 2"


class TestBuildDublinPatterns:
    def test_returns_dict(self):
        patterns = build_dublin_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) == 22  # 1-9, 10-18, 20, 22, 24, 6W = 22 districts

    def test_all_districts_present(self):
        patterns = build_dublin_patterns()
        expected = [
            "Dublin 1", "Dublin 2", "Dublin 3", "Dublin 4", "Dublin 5",
            "Dublin 6", "Dublin 6W", "Dublin 7", "Dublin 8", "Dublin 9",
            "Dublin 10", "Dublin 11", "Dublin 12", "Dublin 13", "Dublin 14",
            "Dublin 15", "Dublin 16", "Dublin 17", "Dublin 18",
            "Dublin 20", "Dublin 22", "Dublin 24",
        ]
        for label in expected:
            assert label in patterns


class TestMatchEircode:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("D01 AB12", "Dublin 1"),
            ("D02YX88", "Dublin 2"),
            ("D10 HK45", "Dublin 10"),
            ("D6W AB12", "Dublin 6W"),
            ("A94 XY12", "Blackrock"),
            ("A96 AB34", "Dun Laoghaire"),
        ],
    )
    def test_eircode_matching(self, text, expected):
        eircode_routing = {
            "D01": "Dublin 1",
            "D02": "Dublin 2",
            "D10": "Dublin 10",
            "D6W": "Dublin 6W",
            "A94": "Blackrock",
            "A96": "Dun Laoghaire",
        }
        assert match_eircode(text, eircode_routing) == expected

    def test_eircode_none_input(self):
        assert match_eircode(None, {}) is None

    def test_eircode_no_match(self):
        assert match_eircode("No eircode here", {"D01": "Dublin 1"}) is None


class TestMatchLettershopKeyword:
    KEYWORDS = [
        {"area": "Blackrock", "patterns": ["blackrock"]},
        {"area": "Swords", "patterns": ["swords"]},
        {"area": "Dun Laoghaire", "patterns": ["dun laoghaire", "dún laoghaire"]},
    ]

    def test_simple_match(self):
        assert match_lettershop_keyword("123 Blackrock Road", self.KEYWORDS) == "Blackrock"

    def test_case_insensitive(self):
        assert match_lettershop_keyword("SWORDS MAIN ST", self.KEYWORDS) == "Swords"

    def test_no_match(self):
        assert match_lettershop_keyword("Cork City", self.KEYWORDS) is None

    def test_none_input(self):
        assert match_lettershop_keyword(None, self.KEYWORDS) is None

    def test_dun_laoghaire_variant(self):
        assert match_lettershop_keyword("Dún Laoghaire", self.KEYWORDS) == "Dun Laoghaire"


class TestMatchNationalArea:
    KEYWORDS = [
        {"area": "Cork", "patterns": [r"\bcork\b"]},
        {"area": "Galway", "patterns": [r"\bgalway\b"]},
    ]

    def test_simple_match(self):
        assert match_national_area("123 Main St, Cork", self.KEYWORDS) == "Cork"

    def test_no_match(self):
        assert match_national_area("Dublin 1", self.KEYWORDS) is None

    def test_none_input(self):
        assert match_national_area(None, self.KEYWORDS) is None
