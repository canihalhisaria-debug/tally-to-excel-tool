from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.tally_tool import TallyPhaseOneService

st.set_page_config(page_title="Tally to Excel Automation Tool", page_icon="📊", layout="wide")

st.title("📊 Tally to Excel Automation Tool — Phase 1")
st.caption("Local app for importing Tally-exported files and generating Excel-ready reports.")

with st.sidebar:
    st.header("Workflow")
    st.markdown(
        """
1. Upload one or more Tally export files (`.csv`, `.xlsx`, `.xls`).
2. Validate standardized transactions preview.
3. Generate Ledger, Voucher, Purchase, and Sales reports.
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

st.subheader("Standardized Transactions")
st.dataframe(standardized.transactions, use_container_width=True, height=300)

st.subheader("Generated Reports")
for report_name, report_df in report_bundle.reports.items():
    with st.expander(f"{report_name} ({len(report_df)} rows)", expanded=report_name == "Ledger Report"):
        st.dataframe(report_df, use_container_width=True, height=260)

filename = f"tally_phase1_reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
st.download_button(
    label="⬇️ Download Formatted Excel Workbook",
    data=excel_bytes,
    file_name=filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.success("Phase 1 report generation complete. Architecture is ready for future modules.")

if st.checkbox("Show schema details", value=False):
    st.write("Transactions schema")
    schema_df = pd.DataFrame({"Column": standardized.transactions.columns, "Dtype": standardized.transactions.dtypes.astype(str)})
    st.dataframe(schema_df, use_container_width=True)
