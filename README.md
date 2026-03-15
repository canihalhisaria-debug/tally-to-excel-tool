# Tally to Excel Automation Tool

Phase 1 local application built with **Python + Streamlit + pandas + openpyxl**.

## Extended Features
- Import one or multiple Tally-exported files (`.csv`, `.xlsx`, `.xls`, `.xlsm`, `.xml`)
- Standardize transaction columns into a canonical dataset
- Polished Streamlit UI with branding/logo support
- Better interactive filters with saved presets
- Preview search for Narration/Voucher/Ledger
- Generate reports:
  - Dashboard
  - Summary KPIs
  - Suspicious Transactions
  - Duplicate Transactions
  - Error Logs
  - Ledger Report
  - Voucher Register
  - Purchase Register
  - Sales Register
  - Expense Head Analysis
  - Journal Voucher Expense
  - GST Summary
  - Party-wise Summary
- Export a formatted multi-sheet Excel workbook with export history tracking in UI
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
    ├── xml_importer.py
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
