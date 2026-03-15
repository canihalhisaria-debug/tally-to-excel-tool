from __future__ import annotations

from datetime import datetime
from io import StringIO

import pandas as pd
import streamlit as st

from src.tally_tool import TallyPhaseOneService

st.set_page_config(page_title="Tally to Excel Automation Tool", page_icon="📊", layout="wide")

st.markdown(
    """
<style>
.main-title {
    font-size: 2rem;
    font-weight: 700;
    margin-bottom: 0;
}
.sub-title {
    color: #5a6a85;
    margin-top: .2rem;
}
.card {
    border: 1px solid #e6e9ef;
    border-radius: 12px;
    padding: 0.9rem 1rem;
    background: #fafbfd;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown("<p class='main-title'>📊 Tally to Excel Automation Tool</p>", unsafe_allow_html=True)
st.markdown(
    "<p class='sub-title'>Polished local app for advanced Tally preview, anomaly checks, and Excel export.</p>",
    unsafe_allow_html=True,
)

if "export_history" not in st.session_state:
    st.session_state.export_history = []
if "presets" not in st.session_state:
    st.session_state.presets = {}

with st.sidebar:
    st.header("Workflow")
    st.markdown(
        """
1. Upload one or more Tally export files (`.csv`, `.xlsx`, `.xls`, `.xml`).
2. Apply filters and optional saved presets.
3. Review previews, KPIs, suspicious flags, and duplicates.
4. Export workbook and track export history.
        """
    )

    st.subheader("Branding")
    brand_name = st.text_input("Brand name", value="Your Business")
    logo_file = st.file_uploader("Upload logo (PNG/JPG)", type=["png", "jpg", "jpeg"], accept_multiple_files=False)
    if logo_file:
        st.image(logo_file.getvalue(), caption=f"{brand_name} logo", use_container_width=True)

uploaded = st.file_uploader(
    "Upload Tally export file(s)",
    type=["csv", "xlsx", "xls", "xlsm", "xml"],
    accept_multiple_files=True,
)


def _demo_payload() -> list[tuple[str, bytes]]:
    """Provide a tiny in-memory dataset so users can explore the UI without real files."""

    sample_csv = StringIO(
        "Date,Voucher Type,Voucher No,Ledger,Party,Narration,Debit,Credit\n"
        "2025-01-01,Sales,1001,Sales A/c,ABC Traders,Invoice INV-1001,25000,0\n"
        "2025-01-01,Receipt,RCPT-01,Cash,ABC Traders,Payment received,0,15000\n"
        "2025-01-02,Purchase,2001,Purchase A/c,XYZ Supplies,Office stationery,0,5200\n"
        "2025-01-03,Journal,JV-09,Indirect Expenses,,Round-off entry,450,0\n"
        "2025-01-03,Sales,1002,Sales A/c,LMN Retail,Invoice INV-1002,18000,0\n"
    ).getvalue()
    return [("demo_transactions.csv", sample_csv.encode("utf-8"))]

source_payload = [(f.name, f.getvalue()) for f in uploaded] if uploaded else []
if not source_payload:
    st.info("Upload at least one file to begin, or use demo mode to preview the software.")
    if st.button("Try demo data"):
        source_payload = _demo_payload()

if not source_payload:
    st.stop()

service = TallyPhaseOneService()

try:
    standardized, report_bundle, excel_bytes = service.run(source_payload)
except Exception as exc:
    st.error(f"Failed to process uploaded files: {exc}")
    st.stop()

transactions = standardized.transactions.copy()

st.subheader("Filter Studio")
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
    amount_series = pd.to_numeric(transactions.get("Amount", pd.Series(dtype=float)), errors="coerce").dropna()
    if amount_series.empty:
        min_amt, max_amt = 0.0, 0.0
    else:
        min_amt, max_amt = float(amount_series.min()), float(amount_series.max())

    if min_amt < max_amt:
        amount_range = st.slider("Amount Range", min_value=min_amt, max_value=max_amt, value=(min_amt, max_amt))
    else:
        amount_range = (min_amt, max_amt)
        st.caption("Amount range filter is fixed because all transactions have the same amount.")

selected_dates = None
if "Date" in transactions and transactions["Date"].notna().any():
    min_date = transactions["Date"].min().date()
    max_date = transactions["Date"].max().date()
    selected_dates = st.date_input("Date Range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

search_text = st.text_input("Preview search (Narration / Voucher No / Ledger)", value="").strip().lower()

preset_col1, preset_col2, preset_col3 = st.columns([2, 2, 1])
with preset_col1:
    preset_name = st.text_input("Preset name", value="")
with preset_col2:
    preset_options = ["-- Select preset --"] + sorted(st.session_state.presets.keys())
    selected_preset = st.selectbox("Saved presets", options=preset_options)
with preset_col3:
    if st.button("Save preset") and preset_name:
        st.session_state.presets[preset_name] = {
            "vouchers": selected_vouchers,
            "ledgers": selected_ledgers,
            "parties": selected_parties,
            "amount_range": amount_range,
            "search": search_text,
        }
        st.success(f"Saved preset: {preset_name}")

if st.button("Apply selected preset") and selected_preset != "-- Select preset --":
    preset = st.session_state.presets[selected_preset]
    selected_vouchers = [v for v in preset["vouchers"] if v in voucher_options]
    selected_ledgers = [l for l in preset["ledgers"] if l in ledger_options]
    selected_parties = [p for p in preset["parties"] if p in party_options]
    amount_range = preset["amount_range"]
    search_text = preset["search"]
    st.info(f"Applied preset: {selected_preset}. Re-run or re-select controls to refine.")

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
    for col in ("Narration", "Voucher No", "Ledger"):
        if col in filtered.columns:
            search_mask = search_mask | filtered[col].astype(str).str.lower().str.contains(search_text, na=False)
    filtered = filtered[search_mask]

st.subheader("Summary KPIs")
kpi_df = report_bundle.reports.get("Summary KPIs", pd.DataFrame(columns=["KPI", "Value"]))
kpi_cols = st.columns(min(4, max(1, len(kpi_df))))
for idx, row in kpi_df.head(4).iterrows():
    kpi_cols[idx].metric(str(row["KPI"]), f"{row['Value']:,}" if isinstance(row["Value"], (int, float)) else row["Value"])

with st.expander("All KPI metrics", expanded=False):
    st.dataframe(kpi_df, use_container_width=True, height=220)

st.subheader("Preview Search Results")
st.caption(f"Showing {len(filtered)} rows after filters (out of {len(transactions)}).")
st.dataframe(filtered.head(200), use_container_width=True, height=280)

flags_col, dup_col = st.columns(2)
with flags_col:
    st.markdown("### 🚩 Suspicious Transaction Flags")
    suspicious_df = report_bundle.reports.get("Suspicious Transactions", pd.DataFrame())
    st.dataframe(suspicious_df.head(200), use_container_width=True, height=280)
with dup_col:
    st.markdown("### 🧬 Duplicate Detection")
    duplicates_df = report_bundle.reports.get("Duplicate Transactions", pd.DataFrame())
    st.dataframe(duplicates_df.head(200), use_container_width=True, height=280)

st.subheader("Generated Reports")
for report_name, report_df in report_bundle.reports.items():
    with st.expander(f"{report_name} ({len(report_df)} rows)", expanded=report_name == "Dashboard"):
        st.dataframe(report_df, use_container_width=True, height=240)

filename = f"tally_extended_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
clicked = st.download_button(
    label="⬇️ Download Formatted Excel Workbook",
    data=excel_bytes,
    file_name=filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
if clicked:
    st.session_state.export_history.insert(
        0,
        {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "File": filename,
            "Brand": brand_name,
            "Rows Exported": len(filtered),
            "Suspicious Rows": len(report_bundle.reports.get("Suspicious Transactions", pd.DataFrame())),
        },
    )

st.subheader("Export History")
if st.session_state.export_history:
    st.dataframe(pd.DataFrame(st.session_state.export_history), use_container_width=True, height=220)
else:
    st.info("No exports recorded yet. Download a workbook to populate history.")

st.success("Ready: polished UI, preview search, presets, anomaly reports, KPI dashboard, and export history are enabled.")

if st.checkbox("Show schema details", value=False):
    schema_df = pd.DataFrame({"Column": standardized.transactions.columns, "Dtype": standardized.transactions.dtypes.astype(str)})
    st.dataframe(schema_df, use_container_width=True)
