"""Central configuration for phase-wise extensibility."""

from dataclasses import dataclass, field


@dataclass(slots=True)
class ReportConfig:
    """Configuration object to keep report behavior easy to extend in next phases."""

    purchase_keywords: tuple[str, ...] = ("purchase", "input")
    sales_keywords: tuple[str, ...] = ("sales", "sale", "output")
    journal_keywords: tuple[str, ...] = ("journal", "jv")
    expense_keywords: tuple[str, ...] = (
        "expense",
        "rent",
        "salary",
        "freight",
        "travelling",
        "transport",
        "office",
        "printing",
        "electricity",
        "repair",
        "commission",
        "bank charges",
    )
    date_output_format: str = "DD-MMM-YYYY"
    currency_format: str = "#,##0.00"
    default_sheet_order: list[str] = field(
        default_factory=lambda: [
            "Dashboard",
            "Error Logs",
            "Ledger Report",
            "Voucher Register",
            "Purchase Register",
            "Sales Register",
            "Expense Head Analysis",
            "Journal Voucher Expense",
            "GST Summary",
            "Party-wise Summary",
        ]
    )


DEFAULT_CONFIG = ReportConfig()
