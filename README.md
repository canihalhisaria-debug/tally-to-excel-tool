# Tally to Excel Automation Tool

Phase 1 local application built with **Python + Streamlit + pandas + openpyxl**.

## Phase 1 Features
- Import one or multiple Tally-exported files (`.csv`, `.xlsx`, `.xls`, `.xlsm`)
- Standardize transaction columns into a canonical dataset
- Generate reports:
  - Ledger Report
  - Voucher Register
  - Purchase Register
  - Sales Register
- Export a formatted multi-sheet Excel workbook
- Modular architecture prepared for future phases

## Tech Stack
- Streamlit (local UI)
- pandas (data processing)
- openpyxl (formatted Excel generation)

## Project Structure
```
.
├── app.py
├── requirements.txt
└── src/tally_tool/
    ├── __init__.py
    ├── config.py
    ├── io.py
    ├── models.py
    ├── pipeline.py
    ├── reports.py
    └── excel_exporter.py
```

## Run Locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Extensibility Notes
`TallyPhaseOneService` in `src/tally_tool/pipeline.py` acts as an orchestration boundary so later phases (e.g., validation rules, templates, scheduled jobs, additional report packs) can be plugged in without UI rewrites.
