"""End-to-end integration tests for the full Data-Sorter pipeline."""

import pandas as pd
import pytest
from pathlib import Path

from src.ingest import load_file
from src.detect_columns import detect_columns
from src.build_address import add_combined_address
from src.classifier import Classifier
from src.output import write_output

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_INPUT = FIXTURE_DIR / "sample_input.xlsx"
CONFIG_PATH = Path(__file__).parent.parent / "config" / "rules.yaml"
COLUMNS_CONFIG = Path(__file__).parent.parent / "config" / "columns.yaml"


@pytest.fixture
def pipeline_output(tmp_path):
    """Run the full pipeline and return (output_path, stats, df_data, df_exc, df_summary)."""
    # 1. Load
    df = load_file(SAMPLE_INPUT)

    # 2. Detect columns
    col_map = detect_columns(list(df.columns), COLUMNS_CONFIG)

    # 3. Build combined address
    df = add_combined_address(df, col_map)

    # 4. Classify
    classifier = Classifier(CONFIG_PATH)
    df_classified, df_exceptions = classifier.classify(df, col_map)

    # 5. Write output
    out_path = tmp_path / "output.xlsx"
    stats = write_output(out_path, df_classified, df_exceptions)

    # Read back for assertions
    df_data = pd.read_excel(out_path, sheet_name="Data")
    df_exc = pd.read_excel(out_path, sheet_name="Exceptions")
    df_summary = pd.read_excel(out_path, sheet_name="Summary")

    return out_path, stats, df_data, df_exc, df_summary


class TestEndToEnd:
    def test_output_file_created(self, pipeline_output):
        out_path, *_ = pipeline_output
        assert out_path.exists()

    def test_three_sheets(self, pipeline_output):
        out_path, *_ = pipeline_output
        xl = pd.ExcelFile(out_path)
        assert set(xl.sheet_names) == {"Data", "Exceptions", "Summary"}

    def test_total_reconciliation(self, pipeline_output):
        _, stats, df_data, df_exc, _ = pipeline_output
        assert stats.total_rows == len(df_data) + len(df_exc)
        assert stats.total_rows == 17  # 17 rows in fixture

    def test_dublin_10_not_dublin_1(self, pipeline_output):
        """Critical: Dublin 10 must be labeled 'Dublin 10', not 'Dublin 1'."""
        _, _, df_data, _, _ = pipeline_output
        claire_row = df_data[df_data["First Name"] == "Claire"]
        assert len(claire_row) == 1
        assert claire_row.iloc[0]["Area"] == "Dublin 10"

    def test_dublin_6w(self, pipeline_output):
        _, _, df_data, _, _ = pipeline_output
        david_row = df_data[df_data["First Name"] == "David"]
        assert len(david_row) == 1
        assert david_row.iloc[0]["Area"] == "Dublin 6W"

    def test_dublin_1_rows(self, pipeline_output):
        _, _, df_data, _, _ = pipeline_output
        d1_rows = df_data[df_data["Area"] == "Dublin 1"]
        assert len(d1_rows) == 2  # Alice and Fiona

    def test_blackrock_lettershop(self, pipeline_output):
        _, _, df_data, _, _ = pipeline_output
        helen_row = df_data[df_data["First Name"] == "Helen"]
        assert helen_row.iloc[0]["Area"] == "Blackrock"
        assert helen_row.iloc[0]["Routing"] == "LETTERSHOP"

    def test_cork_national(self, pipeline_output):
        _, _, df_data, _, _ = pipeline_output
        kevin_row = df_data[df_data["First Name"] == "Kevin"]
        assert kevin_row.iloc[0]["Area"] == "Cork"
        assert kevin_row.iloc[0]["Routing"] == "NATIONAL"

    def test_kerry_national(self, pipeline_output):
        _, _, df_data, _, _ = pipeline_output
        kerry_rows = df_data[df_data["Area"] == "Kerry"]
        assert len(kerry_rows) == 2  # Mike and Niamh

    def test_lettershop_sorted_first(self, pipeline_output):
        """All LETTERSHOP rows should appear before NATIONAL rows."""
        _, _, df_data, _, _ = pipeline_output
        routings = df_data["Routing"].tolist()
        first_national = next((i for i, r in enumerate(routings) if r == "NATIONAL"), len(routings))
        last_lettershop = max(
            (i for i, r in enumerate(routings) if r == "LETTERSHOP"), default=-1
        )
        assert last_lettershop < first_national

    def test_exceptions_have_empty_address(self, pipeline_output):
        _, _, _, df_exc, _ = pipeline_output
        # Oscar has empty address fields
        oscar_row = df_exc[df_exc["First Name"] == "Oscar"]
        assert len(oscar_row) == 1
        assert "Empty address" in oscar_row.iloc[0]["Exception Reason"]

    def test_unknown_address_exception(self, pipeline_output):
        """Pat has no country and unrecognizable address → exception."""
        _, _, _, df_exc, _ = pipeline_output
        pat_row = df_exc[df_exc["First Name"] == "Pat"]
        assert len(pat_row) == 1

    def test_summary_totals_match(self, pipeline_output):
        _, _, df_data, df_exc, df_summary = pipeline_output
        total_row = df_summary[df_summary["Label"] == "Total Rows"]
        assert total_row.iloc[0]["Count"] == len(df_data) + len(df_exc)

    def test_no_combined_address_in_output(self, pipeline_output):
        """Internal combined_address column should not appear in output."""
        _, _, df_data, df_exc, _ = pipeline_output
        assert "combined_address" not in df_data.columns
        assert "combined_address" not in df_exc.columns

    def test_compact_dublin15(self, pipeline_output):
        """Gary's 'Dublin15' (no space) should match Dublin 15."""
        _, _, df_data, _, _ = pipeline_output
        gary_row = df_data[df_data["First Name"] == "Gary"]
        assert len(gary_row) == 1
        assert gary_row.iloc[0]["Area"] == "Dublin 15"

    def test_dun_laoghaire(self, pipeline_output):
        _, _, df_data, _, _ = pipeline_output
        jane_row = df_data[df_data["First Name"] == "Jane"]
        assert len(jane_row) == 1
        assert jane_row.iloc[0]["Area"] == "Dun Laoghaire"
        assert jane_row.iloc[0]["Routing"] == "LETTERSHOP"

    def test_ireland_other_fallback(self, pipeline_output):
        """Rachel has Ireland country but vague address → Ireland Other."""
        _, _, df_data, _, _ = pipeline_output
        rachel_row = df_data[df_data["First Name"] == "Rachel"]
        assert len(rachel_row) == 1
        assert rachel_row.iloc[0]["Area"] == "Ireland Other"
        assert rachel_row.iloc[0]["Routing"] == "NATIONAL"
