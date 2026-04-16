"""Formatting helpers for the output and report agents."""

from __future__ import annotations

from agents.schemas import ComparisonTableRow, WinnerDetails


def format_currency(amount: float) -> str:
    """Format a numeric amount in USD."""

    return f"${amount:,.2f}"


def build_plain_language_summary(winner: WinnerDetails, comparison_table: list[ComparisonTableRow]) -> str:
    """Create a short, user-facing summary of the result."""

    alternative_count = max(0, len(comparison_table) - 1)
    compliance_phrase = "compliant" if winner.is_compliant else "non-compliant"
    return (
        f"{winner.label} is the recommended customs strategy with HS code {winner.hs_code}. "
        f"It was selected because it offers the strongest balance of compliance, landed cost, and risk, "
        f"with a {compliance_phrase} posture, estimated duty of {format_currency(winner.estimated_duty_usd)}, "
        f"and total landed cost of {format_currency(winner.total_landed_cost_usd)}. "
        f"{alternative_count} alternative world(s) were considered."
    )
