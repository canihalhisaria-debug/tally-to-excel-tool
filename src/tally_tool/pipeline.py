"""Orchestration pipeline for import -> reports -> excel export."""

from __future__ import annotations

from .config import DEFAULT_CONFIG, ReportConfig
from .excel_exporter import build_excel_report
from .io import standardize_transactions
from .models import ReportBundle, StandardizedData
from .reports import generate_registers


class TallyPhaseOneService:
    """Application service boundary, intentionally isolated for future phases."""

    def __init__(self, config: ReportConfig = DEFAULT_CONFIG):
        self.config = config

    def run(self, uploaded_files: list[tuple[str, bytes]]) -> tuple[StandardizedData, ReportBundle, bytes]:
        standardized_df = standardize_transactions(uploaded_files)
        reports = generate_registers(standardized_df, self.config)
        excel_bytes = build_excel_report(reports, self.config)

        return StandardizedData(standardized_df), ReportBundle(reports), excel_bytes
