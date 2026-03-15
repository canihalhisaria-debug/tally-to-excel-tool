"""Report generation logic for phase 2 extensions."""

from __future__ import annotations

import re

import pandas as pd

from .config import ReportConfig



def _match_any_keyword(series: pd.Series, keywords: tuple[str, ...]) -> pd.Series:
    if series.empty:
        return pd.Series(dtype=bool)
    if not keywords:
        return pd.Series([False] * len(series), index=series.index)
    pattern = "|".join(re.escape(k.lower()) for k in keywords)
    return series.astype(str).str.lower().str.contains(pattern, na=False, regex=True)


def _keyword_filter(frame: pd.DataFrame, keywords: tuple[str, ...], columns: tuple[str, ...] = ("Voucher Type",)) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    available_cols = [col for col in columns if col in frame.columns]
    if not available_cols:
        return frame.iloc[0:0].copy()

    mask = pd.Series([False] * len(frame), index=frame.index)
    for col in available_cols:
        mask = mask | _match_any_keyword(frame[col], keywords)

    return frame.loc[mask].copy()


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


def generate_expense_head_analysis(transactions: pd.DataFrame, config: ReportConfig) -> pd.DataFrame:
    expense_rows = _keyword_filter(
        transactions,
        config.expense_keywords,
        columns=("Ledger", "Narration", "Voucher Type"),
    )

    if expense_rows.empty:
        return pd.DataFrame(columns=["Expense Head", "Transactions", "Total_Debit", "Total_Credit", "Net_Expense"])

    expense = (
        expense_rows.groupby("Ledger", dropna=False, as_index=False)
        .agg(
            Transactions=("Voucher No", "count"),
            Total_Debit=("Debit", "sum"),
            Total_Credit=("Credit", "sum"),
        )
        .rename(columns={"Ledger": "Expense Head"})
    )
    expense["Net_Expense"] = expense["Total_Debit"] - expense["Total_Credit"]
    return expense.sort_values("Net_Expense", ascending=False)


def generate_journal_voucher_expense(transactions: pd.DataFrame, config: ReportConfig) -> pd.DataFrame:
    journal_rows = _keyword_filter(transactions, config.journal_keywords, columns=("Voucher Type",))
    expense_journal = _keyword_filter(
        journal_rows,
        config.expense_keywords,
        columns=("Ledger", "Narration"),
    )
    return generate_voucher_register(expense_journal)


def generate_gst_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame(columns=["GST_Component", "Amount"])

    ledger_series = transactions["Ledger"] if "Ledger" in transactions.columns else pd.Series("", index=transactions.index)
    gst = pd.DataFrame(
        {
            "GST_Component": ["CGST", "SGST", "IGST"],
            "Amount": [
                transactions.loc[_match_any_keyword(ledger_series, ("cgst",)), "Amount"].sum(),
                transactions.loc[_match_any_keyword(ledger_series, ("sgst", "utgst")), "Amount"].sum(),
                transactions.loc[_match_any_keyword(ledger_series, ("igst",)), "Amount"].sum(),
            ],
        }
    )
    gst["Amount"] = gst["Amount"].abs()
    gst = gst[gst["Amount"] != 0]
    if gst.empty:
        gst = pd.DataFrame([{"GST_Component": "No GST rows detected", "Amount": 0.0}])

    total_row = pd.DataFrame([{"GST_Component": "Total GST", "Amount": gst["Amount"].sum()}])
    return pd.concat([gst, total_row], ignore_index=True)


def generate_party_wise_summary(transactions: pd.DataFrame) -> pd.DataFrame:
    if "Party" not in transactions.columns:
        return pd.DataFrame(columns=["Party", "Transactions", "Total_Debit", "Total_Credit", "Net_Amount"])

    party = (
        transactions.groupby("Party", dropna=False, as_index=False)
        .agg(
            Transactions=("Voucher No", "count"),
            Total_Debit=("Debit", "sum"),
            Total_Credit=("Credit", "sum"),
            Net_Amount=("Amount", "sum"),
        )
        .sort_values("Net_Amount", ascending=False)
    )
    return party


def generate_dashboard(transactions: pd.DataFrame, reports: dict[str, pd.DataFrame]) -> pd.DataFrame:
    total_debit = float(transactions["Debit"].sum()) if "Debit" in transactions else 0.0
    total_credit = float(transactions["Credit"].sum()) if "Credit" in transactions else 0.0
    voucher_count = int(transactions["Voucher No"].nunique()) if "Voucher No" in transactions else 0

    data = [
        ("Total Transactions", len(transactions)),
        ("Unique Vouchers", voucher_count),
        ("Total Debit", total_debit),
        ("Total Credit", total_credit),
        ("Ledger Heads", reports.get("Ledger Report", pd.DataFrame()).shape[0]),
        ("Expense Heads", reports.get("Expense Head Analysis", pd.DataFrame()).shape[0]),
        ("Distinct Parties", reports.get("Party-wise Summary", pd.DataFrame()).shape[0]),
    ]

    return pd.DataFrame(data, columns=["Metric", "Value"])


def generate_error_logs(transactions: pd.DataFrame) -> pd.DataFrame:
    logs: list[dict[str, object]] = []

    if transactions.empty:
        return pd.DataFrame([{"Level": "Warning", "Issue": "No transactions available.", "Count": 0}])

    missing_date = transactions["Date"].isna().sum() if "Date" in transactions else len(transactions)
    if missing_date:
        logs.append({"Level": "Error", "Issue": "Missing/invalid Date", "Count": int(missing_date)})

    missing_ledger = transactions["Ledger"].isna().sum() if "Ledger" in transactions else len(transactions)
    if missing_ledger:
        logs.append({"Level": "Error", "Issue": "Missing Ledger", "Count": int(missing_ledger)})

    missing_vtype = transactions["Voucher Type"].isna().sum() if "Voucher Type" in transactions else len(transactions)
    if missing_vtype:
        logs.append({"Level": "Error", "Issue": "Missing Voucher Type", "Count": int(missing_vtype)})

    zero_amount = (transactions.get("Amount", pd.Series(dtype=float)) == 0).sum()
    if zero_amount:
        logs.append({"Level": "Warning", "Issue": "Zero Amount transactions", "Count": int(zero_amount)})

    duplicates = transactions.duplicated(subset=[c for c in ("Date", "Voucher No", "Ledger", "Amount") if c in transactions.columns]).sum()
    if duplicates:
        logs.append({"Level": "Warning", "Issue": "Potential duplicate transactions", "Count": int(duplicates)})

    if not logs:
        logs.append({"Level": "Info", "Issue": "No data quality issues found.", "Count": 0})

    return pd.DataFrame(logs)


def generate_registers(transactions: pd.DataFrame, config: ReportConfig) -> dict[str, pd.DataFrame]:
    purchase = _keyword_filter(transactions, config.purchase_keywords, columns=("Voucher Type", "Ledger", "Narration"))
    sales = _keyword_filter(transactions, config.sales_keywords, columns=("Voucher Type", "Ledger", "Narration"))

    reports = {
        "Ledger Report": generate_ledger_report(transactions),
        "Voucher Register": generate_voucher_register(transactions),
        "Purchase Register": generate_voucher_register(purchase),
        "Sales Register": generate_voucher_register(sales),
        "Expense Head Analysis": generate_expense_head_analysis(transactions, config),
        "Journal Voucher Expense": generate_journal_voucher_expense(transactions, config),
        "GST Summary": generate_gst_summary(transactions),
        "Party-wise Summary": generate_party_wise_summary(transactions),
        "Error Logs": generate_error_logs(transactions),
    }
    reports["Dashboard"] = generate_dashboard(transactions, reports)
    return reports
