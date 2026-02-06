"""Tests for the output writer."""

import pandas as pd
import pytest
from pathlib import Path

from src.output import write_output, _compute_stats, _build_summary_df
from src.models import PipelineStats


@pytest.fixture
def sample_classified():
    return pd.DataFrame({
        "Name": ["Alice", "Bob", "Charlie"],
        "Address": ["Dublin 1", "Dublin 10", "Cork"],
        "combined_address": ["Dublin 1", "Dublin 10", "Cork"],
        "Lettershop Area": ["Dublin 1", "Dublin 10", "Cork"],
        "Routing": ["LETTERSHOP", "LETTERSHOP", "NATIONAL"],
    })


@pytest.fixture
def sample_exceptions():
    return pd.DataFrame({
        "Name": ["Dave"],
        "Address": [""],
        "combined_address": [""],
        "Lettershop Area": [""],
        "Routing": [""],
        "_exception_reason": ["Empty address"],
    })


class TestWriteOutput:
    def test_creates_file(self, tmp_path, sample_classified, sample_exceptions):
        out_path = tmp_path / "output.xlsx"
        write_output(out_path, sample_classified, sample_exceptions)
        assert out_path.exists()

    def test_three_sheets(self, tmp_path, sample_classified, sample_exceptions):
        out_path = tmp_path / "output.xlsx"
        write_output(out_path, sample_classified, sample_exceptions)
        xl = pd.ExcelFile(out_path)
        assert set(xl.sheet_names) == {"Data", "Exceptions", "Summary"}

    def test_data_sheet_no_internal_columns(self, tmp_path, sample_classified, sample_exceptions):
        out_path = tmp_path / "output.xlsx"
        write_output(out_path, sample_classified, sample_exceptions)
        df = pd.read_excel(out_path, sheet_name="Data")
        assert "combined_address" not in df.columns
        assert "_exception_reason" not in df.columns
        assert "Lettershop Area" in df.columns
        assert "Routing" in df.columns

    def test_exceptions_sheet_has_reason(self, tmp_path, sample_classified, sample_exceptions):
        out_path = tmp_path / "output.xlsx"
        write_output(out_path, sample_classified, sample_exceptions)
        df = pd.read_excel(out_path, sheet_name="Exceptions")
        assert "Exception Reason" in df.columns
        assert "_exception_reason" not in df.columns

    def test_summary_sheet_counts(self, tmp_path, sample_classified, sample_exceptions):
        out_path = tmp_path / "output.xlsx"
        stats = write_output(out_path, sample_classified, sample_exceptions)
        df = pd.read_excel(out_path, sheet_name="Summary")

        # Check total reconciliation
        total_row = df[df["Label"] == "Total Rows"]
        assert total_row.iloc[0]["Count"] == 4

        classified_row = df[df["Label"] == "Classified Rows"]
        assert classified_row.iloc[0]["Count"] == 3

        exception_row = df[df["Label"] == "Exception Rows"]
        assert exception_row.iloc[0]["Count"] == 1

        # Check Routing rows exist
        routing_rows = df[df["Category"] == "Routing"]
        assert len(routing_rows) == 2  # LETTERSHOP and NATIONAL
        assert set(routing_rows["Label"]) == {"LETTERSHOP", "NATIONAL"}

        # Check Percentage column exists
        assert "Percentage" in df.columns

    def test_returns_stats(self, tmp_path, sample_classified, sample_exceptions):
        out_path = tmp_path / "output.xlsx"
        stats = write_output(out_path, sample_classified, sample_exceptions)
        assert isinstance(stats, PipelineStats)
        assert stats.total_rows == 4
        assert stats.classified_rows == 3
        assert stats.exception_rows == 1
        assert stats.area_counts["Dublin 1"] == 1
        assert stats.area_counts["Dublin 10"] == 1
        assert stats.area_counts["Cork"] == 1
        assert stats.routing_counts["LETTERSHOP"] == 2
        assert stats.routing_counts["NATIONAL"] == 1

    def test_empty_exceptions(self, tmp_path, sample_classified):
        """Should work with no exceptions."""
        out_path = tmp_path / "output.xlsx"
        empty_exc = pd.DataFrame(columns=["Name", "_exception_reason"])
        stats = write_output(out_path, sample_classified, empty_exc)
        assert stats.exception_rows == 0

    def test_empty_classified(self, tmp_path, sample_exceptions):
        """Should work with no classified rows."""
        out_path = tmp_path / "output.xlsx"
        empty_cls = pd.DataFrame(columns=["Name", "Lettershop Area", "Routing"])
        stats = write_output(out_path, empty_cls, sample_exceptions)
        assert stats.classified_rows == 0


class TestComputeStats:
    def test_basic(self, sample_classified, sample_exceptions):
        stats = _compute_stats(sample_classified, sample_exceptions)
        assert stats.total_rows == 4
        assert stats.classified_rows == 3
        assert stats.exception_rows == 1

    def test_empty_dfs(self):
        empty = pd.DataFrame(columns=["Lettershop Area"])
        stats = _compute_stats(empty, empty)
        assert stats.total_rows == 0


class TestBuildSummaryDf:
    def test_structure(self):
        stats = PipelineStats(
            total_rows=10,
            classified_rows=8,
            exception_rows=2,
            area_counts={"Dublin 1": 3, "Cork": 5},
            routing_counts={"LETTERSHOP": 3, "NATIONAL": 5},
        )
        df = _build_summary_df(stats)
        assert "Category" in df.columns
        assert "Label" in df.columns
        assert "Count" in df.columns
        assert "Percentage" in df.columns
        # 2 areas + 2 routing + 3 totals = 7
        assert len(df) == 7

        # Verify Routing rows
        routing_rows = df[df["Category"] == "Routing"]
        assert len(routing_rows) == 2
        assert set(routing_rows["Label"]) == {"LETTERSHOP", "NATIONAL"}

        # Verify percentages
        lettershop_row = df[(df["Category"] == "Routing") & (df["Label"] == "LETTERSHOP")]
        assert lettershop_row.iloc[0]["Percentage"] == "37.5%"

        # Verify total rows have empty percentage
        total_rows = df[df["Category"] == "Total"]
        assert all(p == "" for p in total_rows["Percentage"])
