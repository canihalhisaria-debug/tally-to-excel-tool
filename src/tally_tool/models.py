"""Data contracts used across ingestion, report generation, and export."""

from dataclasses import dataclass

import pandas as pd


@dataclass(slots=True)
class StandardizedData:
    """Canonical transaction dataset used by all phase-1 reports."""

    transactions: pd.DataFrame


@dataclass(slots=True)
class ReportBundle:
    """Collection of generated report dataframes keyed by report name."""

    reports: dict[str, pd.DataFrame]
