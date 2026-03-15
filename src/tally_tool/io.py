"""File ingestion and standardization helpers."""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from .xml_importer import parse_tally_xml

CANONICAL_COLUMNS = {
    "date": "Date",
    "voucher date": "Date",
    "voucherdate": "Date",
    "ledger": "Ledger",
    "particulars": "Ledger",
    "account": "Ledger",
    "voucher type": "Voucher Type",
    "vch type": "Voucher Type",
    "type": "Voucher Type",
    "voucher no": "Voucher No",
    "voucher number": "Voucher No",
    "vch no": "Voucher No",
    "debit": "Debit",
    "dr": "Debit",
    "credit": "Credit",
    "cr": "Credit",
    "amount": "Amount",
    "party": "Party",
    "party name": "Party",
    "narration": "Narration",
}

REQUIRED_BASE_COLUMNS = ["Date", "Ledger", "Voucher Type"]


def _normalize_header(value: str) -> str:
    return " ".join(str(value).strip().lower().split())


def _read_file_content(content: bytes, name: str) -> pd.DataFrame:
    if name.lower().endswith(".csv"):
        return pd.read_csv(BytesIO(content))
    if name.lower().endswith((".xlsx", ".xlsm", ".xls")):
        return pd.read_excel(BytesIO(content))
    if name.lower().endswith(".xml"):
        return parse_tally_xml(content)
    raise ValueError(f"Unsupported file type for '{name}'. Use CSV, Excel, or XML.")


def standardize_transactions(uploaded_files: list[tuple[str, bytes]]) -> pd.DataFrame:
    """Read one or more source files into a canonical transaction structure."""

    frames: list[pd.DataFrame] = []
    for filename, content in uploaded_files:
        frame = _read_file_content(content, filename)
        frame.columns = [CANONICAL_COLUMNS.get(_normalize_header(c), str(c).strip()) for c in frame.columns]
        frame["Source File"] = filename
        frames.append(frame)

    if not frames:
        return pd.DataFrame(columns=[*REQUIRED_BASE_COLUMNS, "Source File"])

    merged = pd.concat(frames, ignore_index=True)

    for column in REQUIRED_BASE_COLUMNS:
        if column not in merged.columns:
            merged[column] = pd.NA

    if "Date" in merged.columns:
        merged["Date"] = pd.to_datetime(merged["Date"], errors="coerce")

    for numeric_col in ("Debit", "Credit", "Amount"):
        if numeric_col in merged.columns:
            merged[numeric_col] = pd.to_numeric(merged[numeric_col], errors="coerce").fillna(0.0)
        else:
            merged[numeric_col] = 0.0

    merged["Amount"] = merged["Amount"].where(merged["Amount"].ne(0), merged["Debit"] - merged["Credit"])

    preferred_order = [
        "Date",
        "Voucher Type",
        "Voucher No",
        "Ledger",
        "Party",
        "Narration",
        "Debit",
        "Credit",
        "Amount",
        "Source File",
    ]
    existing = [c for c in preferred_order if c in merged.columns]
    remaining = [c for c in merged.columns if c not in existing]
    return merged[existing + remaining].sort_values(by=["Date", "Voucher No"], na_position="last")
