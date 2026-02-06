"""Output writer — produces a 3-sheet Excel workbook."""

from pathlib import Path

import pandas as pd

from src.models import PipelineStats


def write_output(
    path: str | Path,
    df_classified: pd.DataFrame,
    df_exceptions: pd.DataFrame,
) -> PipelineStats:
    """Write classified data to a 3-sheet Excel workbook.

    Sheet "Data": Original columns + Lettershop Area + Routing, sorted
                  (LETTERSHOP first, then by area).
    Sheet "Exceptions": Failed rows with reason column.
    Sheet "Summary": Counts per area, exception count, total reconciliation.

    Returns PipelineStats with summary counts.
    """
    path = Path(path)

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
    if "Lettershop Area" in df_classified.columns and classified_count > 0:
        area_counts = df_classified["Lettershop Area"].value_counts().to_dict()

    return PipelineStats(
        total_rows=classified_count + exception_count,
        classified_rows=classified_count,
        exception_rows=exception_count,
        area_counts=area_counts,
    )


def _build_summary_df(stats: PipelineStats) -> pd.DataFrame:
    """Build the summary sheet DataFrame."""
    rows = []

    # Area breakdown
    for area, count in sorted(stats.area_counts.items()):
        rows.append({"Category": "Area", "Label": area, "Count": count})

    # Totals
    rows.append({"Category": "Total", "Label": "Classified Rows", "Count": stats.classified_rows})
    rows.append({"Category": "Total", "Label": "Exception Rows", "Count": stats.exception_rows})
    rows.append({"Category": "Total", "Label": "Total Rows", "Count": stats.total_rows})

    return pd.DataFrame(rows)
