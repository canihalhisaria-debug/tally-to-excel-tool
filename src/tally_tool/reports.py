"""Report generation logic for phase 1."""

from __future__ import annotations

import pandas as pd

from .config import ReportConfig


def generate_ledger_report(transactions: pd.DataFrame) -> pd.DataFrame:
    ledger = (
        transactions.groupby("Ledger", dropna=False, as_index=False)
        .agg(
            Transactions=("Voucher No", "count"),
            Total_Debit=("Debit", "sum"),
            Total_Credit=("Credit", "sum"),
            Net_Amount=("Amount", "sum"),
        )
        .sort_values("Net_Amount", ascending=False)
    )
    return ledger


def generate_voucher_register(transactions: pd.DataFrame) -> pd.DataFrame:
    cols = [
        c
        for c in ["Date", "Voucher Type", "Voucher No", "Ledger", "Party", "Narration", "Debit", "Credit", "Amount", "Source File"]
        if c in transactions.columns
    ]
    return transactions[cols].copy()


def _keyword_filter(frame: pd.DataFrame, keywords: tuple[str, ...]) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    pattern = "|".join(keywords)
    mask = frame["Voucher Type"].astype(str).str.lower().str.contains(pattern, na=False)
    return frame.loc[mask].copy()


def generate_registers(transactions: pd.DataFrame, config: ReportConfig) -> dict[str, pd.DataFrame]:
    purchase = _keyword_filter(transactions, config.purchase_keywords)
    sales = _keyword_filter(transactions, config.sales_keywords)

    return {
        "Ledger Report": generate_ledger_report(transactions),
        "Voucher Register": generate_voucher_register(transactions),
        "Purchase Register": generate_voucher_register(purchase),
        "Sales Register": generate_voucher_register(sales),
    }
