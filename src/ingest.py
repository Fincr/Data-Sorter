"""File ingestion — load Excel (.xlsx) and CSV files into DataFrames."""

from pathlib import Path

import pandas as pd

from src.exceptions import FileFormatError

SUPPORTED_EXTENSIONS = {".xlsx", ".xls", ".csv"}


def load_file(path: str | Path) -> pd.DataFrame:
    """Load a spreadsheet file into a DataFrame.

    Supports .xlsx (openpyxl engine), .xls, and .csv (with encoding sniffing).
    Strips whitespace from column headers.
    """
    path = Path(path)

    if not path.exists():
        raise FileFormatError(f"File not found: {path}")

    ext = path.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise FileFormatError(
            f"Unsupported file format '{ext}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    try:
        if ext == ".csv":
            df = _load_csv(path)
        elif ext == ".xlsx":
            df = pd.read_excel(path, engine="openpyxl")
        elif ext == ".xls":
            df = pd.read_excel(path)
        else:
            raise FileFormatError(f"Unsupported extension: {ext}")
    except FileFormatError:
        raise
    except Exception as e:
        raise FileFormatError(f"Failed to read {path.name}: {e}")

    # Strip whitespace from column headers
    df.columns = [str(c).strip() for c in df.columns]

    if df.empty:
        raise FileFormatError(f"File is empty: {path.name}")

    return df


def _load_csv(path: Path) -> pd.DataFrame:
    """Load CSV with encoding detection fallback."""
    # Try UTF-8 first, then fall back to latin-1 (accepts any byte)
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, encoding=encoding, dtype=str)
        except UnicodeDecodeError:
            continue

    raise FileFormatError(f"Could not decode CSV file: {path.name}")
