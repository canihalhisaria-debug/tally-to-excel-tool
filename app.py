from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.tally_tool import TallyPhaseOneService

st.set_page_config(page_title="Tally to Excel Automation Tool", page_icon="📊", layout="wide")

st.title("📊 Tally to Excel Automation Tool — Extended Reporting")
st.caption("Local app for importing Tally-exported files and generating advanced Excel-ready reports.")

with st.sidebar:
    st.header("Workflow")
    st.markdown(
        """
1. Upload one or more Tally export files (`.csv`, `.xlsx`, `.xls`).
2. Apply filters to standardized transactions.
3. Generate Ledger, Voucher, GST, Expense, Party-wise, Dashboard and Error Log reports.
4. Download the formatted Excel workbook.
        """
    )

uploaded = st.file_uploader(
    "Upload Tally export file(s)",
    type=["csv", "xlsx", "xls", "xlsm"],
    accept_multiple_files=True,
)

if not uploaded:
    st.info("Upload at least one file to begin.")
    st.stop()

service = TallyPhaseOneService()
source_payload = [(f.name, f.getvalue()) for f in uploaded]

try:
    standardized, report_bundle, excel_bytes = service.run(source_payload)
except Exception as exc:
    st.error(f"Failed to process uploaded files: {exc}")
    st.stop()

st.subheader("Better Filters")
transactions = standardized.transactions.copy()

col1, col2, col3, col4 = st.columns(4)
with col1:
    voucher_options = sorted([x for x in transactions["Voucher Type"].dropna().astype(str).unique()]) if "Voucher Type" in transactions else []
    selected_vouchers = st.multiselect("Voucher Type", options=voucher_options, default=[])
with col2:
    ledger_options = sorted([x for x in transactions["Ledger"].dropna().astype(str).unique()]) if "Ledger" in transactions else []
    selected_ledgers = st.multiselect("Ledger", options=ledger_options, default=[])
with col3:
    party_options = sorted([x for x in transactions["Party"].dropna().astype(str).unique()]) if "Party" in transactions else []
    selected_parties = st.multiselect("Party", options=party_options, default=[])
with col4:
    amount_range = st.slider(
        "Amount Range",
        min_value=float(transactions["Amount"].min()) if not transactions.empty else 0.0,
        max_value=float(transactions["Amount"].max()) if not transactions.empty else 0.0,
        value=(
            float(transactions["Amount"].min()) if not transactions.empty else 0.0,
            float(transactions["Amount"].max()) if not transactions.empty else 0.0,
        ),
    )

if "Date" in transactions and transactions["Date"].notna().any():
    min_date = transactions["Date"].min().date()
    max_date = transactions["Date"].max().date()
    selected_dates = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
else:
    selected_dates = None

search_text = st.text_input("Search Narration / Voucher No", value="").strip().lower()

filtered = transactions.copy()
if selected_vouchers:
    filtered = filtered[filtered["Voucher Type"].astype(str).isin(selected_vouchers)]
if selected_ledgers:
    filtered = filtered[filtered["Ledger"].astype(str).isin(selected_ledgers)]
if selected_parties:
    filtered = filtered[filtered["Party"].astype(str).isin(selected_parties)]
if not filtered.empty:
    filtered = filtered[(filtered["Amount"] >= amount_range[0]) & (filtered["Amount"] <= amount_range[1])]
if selected_dates and isinstance(selected_dates, tuple) and len(selected_dates) == 2 and "Date" in filtered:
    start_date, end_date = pd.to_datetime(selected_dates[0]), pd.to_datetime(selected_dates[1])
    filtered = filtered[(filtered["Date"] >= start_date) & (filtered["Date"] <= end_date)]
if search_text:
    search_mask = pd.Series([False] * len(filtered), index=filtered.index)
    for col in ("Narration", "Voucher No"):
        if col in filtered.columns:
            search_mask = search_mask | filtered[col].astype(str).str.lower().str.contains(search_text, na=False)
    filtered = filtered[search_mask]

st.subheader("Standardized Transactions")
st.caption(f"Showing {len(filtered)} rows after filters (out of {len(transactions)}).")
st.dataframe(filtered, use_container_width=True, height=300)

st.subheader("Generated Reports")
for report_name, report_df in report_bundle.reports.items():
    with st.expander(f"{report_name} ({len(report_df)} rows)", expanded=report_name == "Dashboard"):
        st.dataframe(report_df, use_container_width=True, height=260)

filename = f"tally_extended_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
st.download_button(
    label="⬇️ Download Formatted Excel Workbook",
    data=excel_bytes,
    file_name=filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.success("Extended report generation complete with dashboard, GST, expense analytics, and error logs.")

if st.checkbox("Show schema details", value=False):
    st.write("Transactions schema")
    schema_df = pd.DataFrame({"Column": standardized.transactions.columns, "Dtype": standardized.transactions.dtypes.astype(str)})
    st.dataframe(schema_df, use_container_width=True)
