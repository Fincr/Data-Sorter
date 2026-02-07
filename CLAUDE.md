# Data-Sorter

## Overview
Python CLI/GUI tool that classifies addresses into routing buckets using config-driven YAML rules. Supports multiple carriers: Lettershop Ireland (LETTERSHOP/NATIONAL) and Correos Spain (D1/D2). Ingests messy Excel/CSV data, auto-detects columns, and outputs a clean 3-sheet Excel workbook.

## Quick Reference

### Run tests
```
python -m pytest tests/ -v
```

### CLI usage
```
python app.py input.xlsx output.xlsx
python app.py input.csv output.xlsx --config config/rules.yaml --columns-config config/columns.yaml --log-level DEBUG
```

### GUI
```
streamlit run gui.py
```
- `gui.py` — Landing page (carrier selection)
- `pages/1_Lettershop_Ireland.py` — Ireland address sorter
- `pages/2_Configuration.py` — Config editor
- `pages/3_Correos_Spain.py` — Spain address sorter (D1/D2)

## Architecture

### Pipeline flow
`ingest.py` → `detect_columns.py` → `build_address.py` → `classifier.py` → `output.py`

### Key modules
- `src/ireland.py` — Dublin district regex matching (highest-risk component). Districts checked in descending order with negative lookahead to prevent "Dublin 1" matching "Dublin 10".
- `src/classifier.py` — Ireland rule engine. Dispatches to country handlers via registry pattern. Classification chain: Eircode → Dublin district → lettershop keywords → national areas → fallback.
- `src/spain.py` — Spanish postal code matching. Loads D1 postal codes from YAML and provides lookup.
- `src/spain_classifier.py` — Spain classifier. Routes addresses to D1 (locality name) or D2 based on 5-digit postal code. No valid postcode → Exception.
- `src/detect_columns.py` — Three-pass column matching: exact → normalized → fuzzy (difflib, 75% threshold). Passes run globally across all fields before escalating to next pass.
- `config/rules.yaml` — Ireland classification rules. Non-developers can edit this to add areas/patterns.
- `config/spain_d1.yaml` — Correos Anexo B D1 postal codes (capitals, administrations, cities >50k).
- `config/columns.yaml` — Column name aliases for auto-detection.

### Output format
3-sheet Excel workbook:
- **Data**: Classified rows with Area + Routing columns, sorted by Routing then Area
- **Exceptions**: Failed rows with Exception Reason column
- **Summary**: Area counts + total reconciliation

## Coding Conventions
- Python 3.10+ (type hints, dataclasses)
- No external fuzzy matching library — uses stdlib `difflib.SequenceMatcher`
- Config-driven: rules and column aliases in YAML, not hardcoded
- Exceptions sheet captures all unclassifiable rows with reasons — never silently dropped
- Mergesort for stable ordering within routing groups
