"""Markdown report generation agent."""

from __future__ import annotations

import re

from agents.base.base_agent import BaseAgent
from agents.output.formatter import format_currency
from agents.schemas import ReportInput, ReportResult


class ReportAgent(BaseAgent[ReportInput, ReportResult]):
    """Produce a markdown customs strategy report for downstream PDF generation."""

    agent_name = "report"

    async def run(self, input: ReportInput) -> ReportResult:
        """Render the final result as a markdown report."""

        validated_input = ReportInput.model_validate(input)
        output = validated_input.output_result
        winner = output.winner_details

        comparison_rows = "\n".join(
            [
                (
                    f"| {row.label} | {row.hs_code} | {row.is_compliant} | "
                    f"{row.duty_rate_percent:.2f}% | {format_currency(row.estimated_duty_usd)} | "
                    f"{format_currency(row.total_landed_cost_usd)} | {row.risk_score:.2f} | "
                    f"{row.recommendation} | {row.composite_score:.4f} |"
                )
                for row in output.comparison_table
            ]
        )

        alternative_rows = "\n".join(
            [f"- {item.label} ({item.hs_code}) score {item.composite_score:.4f} [{item.recommendation}]" for item in output.alternatives]
        )
        if not alternative_rows:
            alternative_rows = "- None"

        report_markdown = f"""# Customs Brain Evaluation Report

## Executive Summary
{output.plain_language_summary}

## Recommended World
- World ID: `{winner.world_id}`
- Label: {winner.label}
- Final HS Code: `{winner.hs_code}`
- Product Description: {winner.product_description}
- Destination Country: {winner.destination_country or "Unknown"}
- Compliance Status: {"Compliant" if winner.is_compliant else "Non-compliant"}
- Duty Rate: {winner.duty_rate_percent:.2f}%
- Estimated Duty: {format_currency(winner.estimated_duty_usd)}
- Total Landed Cost: {format_currency(winner.total_landed_cost_usd)}
- Risk Score: {winner.risk_score:.2f}
- Recommendation: {winner.recommendation}

## Meta Reasoning
{output.meta_reasoning}

## Alternatives
{alternative_rows}

## Comparison Table
| World | HS Code | Compliant | Duty Rate | Duty USD | Landed Cost | Risk | Recommendation | Composite |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
{comparison_rows}
"""

        slug_base = re.sub(r"[^a-z0-9]+", "-", winner.product_description.lower()).strip("-") or "shipment"
        filename_suggestion = f"customs-brain-report-{slug_base}-{winner.world_id}.md"
        return ReportResult(
            report_markdown=report_markdown,
            filename_suggestion=filename_suggestion,
        )
