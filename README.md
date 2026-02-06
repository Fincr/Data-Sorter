# Data-Sorter

Address classification tool for logistics routing. Ingests messy address data from Excel/CSV, auto-detects columns, classifies addresses into routing buckets using config-driven rules, and outputs a clean 3-sheet Excel workbook.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### CLI

```bash
python app.py input.xlsx output.xlsx
```

Options:
- `--config PATH` — Custom rules YAML (default: `config/rules.yaml`)
- `--columns-config PATH` — Custom column aliases YAML (default: `config/columns.yaml`)
- `--log-level {DEBUG,INFO,WARNING,ERROR}` — Logging level (default: INFO)

### GUI (Streamlit)

```bash
streamlit run gui.py
```

Upload a file, review detected column mappings, click Process, download the result.

## Output

The output Excel workbook contains three sheets:

| Sheet | Contents |
|-------|----------|
| **Data** | Classified rows with `Lettershop Area` and `Routing` columns, sorted with LETTERSHOP rows first |
| **Exceptions** | Rows that couldn't be classified, with an `Exception Reason` column |
| **Summary** | Row counts per area, exception count, and total reconciliation |

## Classification Logic

1. **Country detection** — from the Country column or by scanning the combined address
2. **Eircode matching** — 3-character prefix maps to area (e.g., D02 → Dublin 2)
3. **Dublin district matching** — regex with descending-order check and negative lookahead to correctly distinguish Dublin 1 from Dublin 10
4. **Lettershop keyword matching** — named areas within the Greater Dublin zone (Blackrock, Swords, etc.)
5. **National area matching** — Irish counties and cities outside Dublin
6. **Fallback** — "Ireland Other" for unmatched Ireland addresses; exceptions for truly unclassifiable rows

## Configuration

### `config/rules.yaml`
Classification rules: country patterns, Eircode routing, Dublin districts, lettershop areas, national areas. Edit this file to add new areas or patterns without touching Python code.

### `config/columns.yaml`
Column name aliases for auto-detection. Supports exact, normalized, and fuzzy matching against spreadsheet headers.

## Tests

```bash
python -m pytest tests/ -v
```

155 tests covering Dublin district edge cases, column detection, address building, classification, output, and full pipeline integration.
