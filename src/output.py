"""Output writer — produces a 3-sheet Excel workbook or 3 CSV files."""

from pathlib import Path

import pandas as pd

from src.models import PipelineStats


def write_output(
    path: str | Path,
    df_classified: pd.DataFrame,
    df_exceptions: pd.DataFrame,
    format: str = "xlsx",
) -> PipelineStats:
    """Write classified data to output file(s).

    When format="xlsx": Single 3-sheet Excel workbook (Data, Exceptions, Summary).
    When format="csv": Three CSV files — {stem}_data.csv, {stem}_exceptions.csv,
                       {stem}_summary.csv.

    Returns PipelineStats with summary counts.
    """
    path = Path(path)

    # Add sequential CPG_UID column to classified data
    if len(df_classified) > 0:
        df_classified = df_classified.copy()
        df_classified["CPG_UID"] = range(1, len(df_classified) + 1)

    # Build summary data
    stats = _compute_stats(df_classified, df_exceptions)
    df_summary = _build_summary_df(stats)

    # Prepare exceptions sheet — rename internal column
    df_exc_output = df_exceptions.copy()
    if "_exception_reason" in df_exc_output.columns:
        df_exc_output = df_exc_output.rename(columns={"_exception_reason": "Exception Reason"})

    # Drop combined_address from output if present (internal column)
    for df in [df_classified, df_exc_output]:
        if "combined_address" in df.columns:
            df.drop(columns=["combined_address"], inplace=True)

    if format == "csv":
        stem = path.parent / path.stem
        data_path = Path(f"{stem}_data.csv")
        exc_path = Path(f"{stem}_exceptions.csv")
        summary_path = Path(f"{stem}_summary.csv")

        df_classified.to_csv(data_path, index=False)
        df_exc_output.to_csv(exc_path, index=False)
        df_summary.to_csv(summary_path, index=False)
    else:
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df_classified.to_excel(writer, sheet_name="Data", index=False)
            df_exc_output.to_excel(writer, sheet_name="Exceptions", index=False)
            df_summary.to_excel(writer, sheet_name="Summary", index=False)

    return stats


def _compute_stats(
    df_classified: pd.DataFrame,
    df_exceptions: pd.DataFrame,
) -> PipelineStats:
    """Compute summary statistics."""
    classified_count = len(df_classified)
    exception_count = len(df_exceptions)

    area_counts: dict[str, int] = {}
    if "Area" in df_classified.columns and classified_count > 0:
        area_counts = df_classified["Area"].value_counts().to_dict()

    routing_counts: dict[str, int] = {}
    if "Routing" in df_classified.columns and classified_count > 0:
        routing_counts = df_classified["Routing"].value_counts().to_dict()

    return PipelineStats(
        total_rows=classified_count + exception_count,
        classified_rows=classified_count,
        exception_rows=exception_count,
        area_counts=area_counts,
        routing_counts=routing_counts,
    )


def _build_summary_df(stats: PipelineStats) -> pd.DataFrame:
    """Build the summary sheet DataFrame."""
    rows = []
    classified = stats.classified_rows

    # Area breakdown
    for area, count in sorted(stats.area_counts.items()):
        pct = (count / classified * 100) if classified > 0 else 0.0
        rows.append({"Category": "Area", "Label": area, "Count": count, "Percentage": f"{pct:.1f}%"})

    # Routing breakdown
    for routing, count in sorted(stats.routing_counts.items()):
        pct = (count / classified * 100) if classified > 0 else 0.0
        rows.append({"Category": "Routing", "Label": routing, "Count": count, "Percentage": f"{pct:.1f}%"})

    # Totals
    rows.append({"Category": "Total", "Label": "Classified Rows", "Count": stats.classified_rows, "Percentage": ""})
    rows.append({"Category": "Total", "Label": "Exception Rows", "Count": stats.exception_rows, "Percentage": ""})
    rows.append({"Category": "Total", "Label": "Total Rows", "Count": stats.total_rows, "Percentage": ""})

    return pd.DataFrame(rows)
