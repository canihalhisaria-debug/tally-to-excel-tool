"""Parser for importing Tally XML exports into canonical transaction rows."""

from __future__ import annotations

from io import BytesIO
import xml.etree.ElementTree as ET

import pandas as pd


def _localname(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def _child_text(element: ET.Element, child_name: str) -> str:
    for child in list(element):
        if _localname(child.tag).upper() == child_name.upper():
            return (child.text or "").strip()
    return ""


def _extract_ledger_entries(voucher_element: ET.Element) -> list[ET.Element]:
    entries: list[ET.Element] = []
    for node in voucher_element.iter():
        tag = _localname(node.tag).upper()
        if tag in {"ALLLEDGERENTRIES.LIST", "LEDGERENTRIES.LIST"}:
            entries.append(node)
    return entries


def _parse_tally_date(raw_date: str) -> pd.Timestamp | pd.NaT:
    cleaned = (raw_date or "").strip()
    if not cleaned:
        return pd.NaT
    if cleaned.isdigit() and len(cleaned) == 8:
        return pd.to_datetime(cleaned, format="%Y%m%d", errors="coerce")
    return pd.to_datetime(cleaned, errors="coerce")


def parse_tally_xml(content: bytes) -> pd.DataFrame:
    """Parse XML bytes and return transaction rows in canonical schema."""

    try:
        root = ET.parse(BytesIO(content)).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Invalid XML content: {exc}") from exc

    rows: list[dict[str, object]] = []

    for element in root.iter():
        tag = _localname(element.tag).upper()
        if tag != "VOUCHER":
            continue

        voucher_no = _child_text(element, "VOUCHERNUMBER")
        voucher_type = _child_text(element, "VOUCHERTYPENAME") or _child_text(element, "VOUCHERTYPE")
        narration = _child_text(element, "NARRATION")
        date = _parse_tally_date(_child_text(element, "DATE"))

        ledger_entries = _extract_ledger_entries(element)

        for entry in ledger_entries:
            ledger_name = _child_text(entry, "LEDGERNAME")
            amount = pd.to_numeric(_child_text(entry, "AMOUNT"), errors="coerce")
            amount_value = float(amount) if pd.notna(amount) else 0.0

            rows.append(
                {
                    "Date": date,
                    "Voucher Type": voucher_type,
                    "Voucher No": voucher_no,
                    "Ledger": ledger_name,
                    "Narration": narration,
                    "Amount": amount_value,
                    "Debit": amount_value if amount_value > 0 else 0.0,
                    "Credit": abs(amount_value) if amount_value < 0 else 0.0,
                }
            )

        if not ledger_entries:
            rows.append(
                {
                    "Date": date,
                    "Voucher Type": voucher_type,
                    "Voucher No": voucher_no,
                    "Ledger": "",
                    "Narration": narration,
                    "Amount": 0.0,
                    "Debit": 0.0,
                    "Credit": 0.0,
                }
            )

    return pd.DataFrame(rows)
