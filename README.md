# Tally to Excel Automation Tool

Backend API built with **Python + FastAPI + pandas + openpyxl**.

## Extended Features
- Import one or multiple Tally-exported files (`.csv`, `.xlsx`, `.xls`, `.xlsm`, `.xml`)
- Standardize transaction columns into a canonical dataset
- FastAPI endpoints for file preview and processing
- Date/voucher-type filters for controlled report generation
- JSON preview response for first 100 rows
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
- Export a formatted multi-sheet Excel workbook with styled sheets
- Modular architecture prepared for future phases

## Tech Stack
- FastAPI (backend API)
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
uvicorn app:app --reload
```


## Public Preview URL (Tunnel)
You can expose the local FastAPI app with a temporary public URL:

```bash
bash scripts/start_public_preview.sh 8501
```

This script starts the app server and then attempts a tunnel in this order:
1. `cloudflared` quick tunnel
2. downloaded `/tmp/cloudflared`
3. `npx localtunnel`

> Note: tunnel availability depends on outbound network access in your environment.

## Extensibility Notes
`TallyPhaseOneService` in `src/tally_tool/pipeline.py` acts as an orchestration boundary so later phases (e.g., validation rules, templates, scheduled jobs, additional report packs) can be plugged in without UI rewrites.


## Render Start Command
```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```
