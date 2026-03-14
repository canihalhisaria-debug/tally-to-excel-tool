"""Central configuration for phase-wise extensibility."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReportConfig:
    """Configuration object to keep report behavior easy to extend in next phases."""

    purchase_keywords: tuple[str, ...] = ("purchase",)
    sales_keywords: tuple[str, ...] = ("sales", "sale")
    date_output_format: str = "DD-MMM-YYYY"
    currency_format: str = "#,##0.00"
    default_sheet_order: list[str] = field(
        default_factory=lambda: [
            "Ledger Report",
            "Voucher Register",
            "Purchase Register",
            "Sales Register",
        ]
    )


DEFAULT_CONFIG = ReportConfig()
