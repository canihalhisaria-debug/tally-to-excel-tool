"""Parser for importing Tally XML exports into canonical transaction rows."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

_INVALID_DECIMAL_ENTITIES = re.compile(
    r"&#(?:0|1|2|3|4|5|6|7|8|11|12|14|15|16|17|18|19|20|21|22|23|24|25|26|27|28|29|30|31);"
)
_INVALID_HEX_ENTITIES = re.compile(
    r"&#x(?:0|1|2|3|4|5|6|7|8|B|C|E|F|10|11|12|13|14|15|16|17|18|19|1A|1B|1C|1D|1E|1F);",
    flags=re.IGNORECASE,
)
_INVALID_XML_CHARS = re.compile(r"[^\x09\x0A\x0D\x20-\uD7FF\uE000-\uFFFD]")


def clean_tally_xml(xml_text: str) -> str:
    """Remove invalid numeric references and disallowed control characters."""

    xml_text = _INVALID_DECIMAL_ENTITIES.sub("", xml_text)
    xml_text = _INVALID_HEX_ENTITIES.sub("", xml_text)
    return _INVALID_XML_CHARS.sub("", xml_text)


def parse_tally_date(raw: str) -> str:
    """Normalize known Tally date formats to ISO-8601 date strings."""

    cleaned = str(raw or "").strip()
    if not cleaned:
        return ""

    for fmt in ("%Y%m%d", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(cleaned, fmt).date().isoformat()
        except ValueError:
            continue
    return cleaned


def node_text(node: ET.Element, tag_name: str) -> str:
    """Read child text for tag_name, returning an empty string when absent."""

    child = node.find(tag_name)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def safe_float(value: str) -> float:
    """Coerce text values to float, returning 0.0 for invalid values."""

    cleaned = str(value or "").strip()
    if not cleaned:
        return 0.0
    try:
        return float(cleaned)
    except (TypeError, ValueError):
        return 0.0


def parse_tally_xml_content(xml_text: str) -> pd.DataFrame:
    """Parse a Tally XML string and return voucher ledger/inventory rows."""

    xml_text = clean_tally_xml(xml_text)

    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ValueError(f"XML parse error: {exc}") from exc

    rows: list[dict[str, Any]] = []

    vouchers = root.findall(".//VOUCHER")
    if not vouchers:
        vouchers = root.findall(".//TALLYMESSAGE/VOUCHER")

    for voucher in vouchers:
        voucher_date = parse_tally_date(node_text(voucher, "DATE"))
        voucher_type = node_text(voucher, "VOUCHERTYPENAME")
        voucher_number = node_text(voucher, "VOUCHERNUMBER")
        narration = node_text(voucher, "NARRATION")
        party_ledger = node_text(voucher, "PARTYLEDGERNAME")
        reference = node_text(voucher, "REFERENCE")
        persisted_view = node_text(voucher, "PERSISTEDVIEW")

        ledger_entries = voucher.findall(".//ALLLEDGERENTRIES.LIST")
        inventory_entries = voucher.findall(".//ALLINVENTORYENTRIES.LIST")

        if not ledger_entries and not inventory_entries:
            rows.append(
                {
                    "Date": voucher_date,
                    "Voucher Type": voucher_type,
                    "Voucher Number": voucher_number,
                    "Party Ledger / Particulars": party_ledger,
                    "Ledger Name": "",
                    "Stock Item": "",
                    "Amount": 0.0,
                    "Dr/Cr": "",
                    "Narration": narration,
                    "Reference": reference,
                    "View": persisted_view,
                }
            )
            continue

        for entry in ledger_entries:
            ledger_name = node_text(entry, "LEDGERNAME")
            amount = safe_float(node_text(entry, "AMOUNT"))
            rows.append(
                {
                    "Date": voucher_date,
                    "Voucher Type": voucher_type,
                    "Voucher Number": voucher_number,
                    "Party Ledger / Particulars": party_ledger,
                    "Ledger Name": ledger_name,
                    "Stock Item": "",
                    "Amount": abs(amount),
                    "Dr/Cr": "Dr" if amount < 0 else "Cr",
                    "Narration": narration,
                    "Reference": reference,
                    "View": persisted_view,
                }
            )

        for item in inventory_entries:
            stock_item = node_text(item, "STOCKITEMNAME")
            amount = safe_float(node_text(item, "AMOUNT"))
            rows.append(
                {
                    "Date": voucher_date,
                    "Voucher Type": voucher_type,
                    "Voucher Number": voucher_number,
                    "Party Ledger / Particulars": party_ledger,
                    "Ledger Name": "",
                    "Stock Item": stock_item,
                    "Amount": abs(amount),
                    "Dr/Cr": "Dr" if amount < 0 else "Cr",
                    "Narration": narration,
                    "Reference": reference,
                    "View": persisted_view,
                }
            )

    return pd.DataFrame(rows)


def parse_tally_xml_file(file_path: str | Path) -> pd.DataFrame:
    """Load and parse a Tally XML file path."""

    raw = Path(file_path).read_bytes()
    xml_text = raw.decode("utf-8", errors="ignore")
    return parse_tally_xml_content(xml_text)


def parse_tally_xml(content: bytes) -> pd.DataFrame:
    """Compatibility wrapper for in-memory XML parsing."""

    xml_text = content.decode("utf-8", errors="ignore")
    return parse_tally_xml_content(xml_text)
