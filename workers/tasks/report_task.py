"""Worker task for report generation and persistence."""

from __future__ import annotations

import os
from pathlib import Path

from agents.report import ReportAgent, ReportInput
from workers.llm import get_agent_kwargs

REPORTS_DIR = Path(os.getenv("REPORT_DIR", "data/reports"))


async def run_report(ctx: dict) -> dict:
    """Generate markdown report content and save it to disk."""

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    agent = ReportAgent(**get_agent_kwargs())
    report_result = await agent.run(ReportInput(output_result=ctx["output_result"]))
    report_path = REPORTS_DIR / report_result.filename_suggestion
    report_path.write_text(report_result.report_markdown, encoding="utf-8")

    return {
        "report_result": report_result,
        "report_path": str(report_path.resolve()),
    }
