"""Build a combined address string from mapped columns."""

import pandas as pd

from src.models import ColumnMapping


def add_combined_address(df: pd.DataFrame, col_map: ColumnMapping) -> pd.DataFrame:
    """Add a 'combined_address' column by concatenating mapped address fields.

    Skips NaN/empty values. Joins with ", " separator.
    Returns a copy of the DataFrame with the new column.
    """
    df = df.copy()
    address_cols = col_map.address_columns()

    if not address_cols:
        df["combined_address"] = ""
        return df

    def _combine_row(row: pd.Series) -> str:
        parts = []
        for col in address_cols:
            val = row.get(col)
            if pd.notna(val):
                val_str = str(val).strip()
                if val_str:
                    parts.append(val_str)
        return ", ".join(parts)

    df["combined_address"] = df.apply(_combine_row, axis=1)
    return df
