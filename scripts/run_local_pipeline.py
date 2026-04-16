"""Run the Customs Brain agent pipeline locally without Redis/Postgres."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

from openai import AsyncOpenAI

from agents.compliance import ComplianceAgent, ComplianceInput
from agents.debate import DebateAgent, DebateInput
from agents.duty import DutyAgent, DutyInput
from agents.extraction import ExtractionAgent, ExtractionInput
from agents.hs_code import HSCodeAgent, HSCodeInput
from agents.meta import MetaAgent, MetaInput
from agents.output import OutputAgent, OutputInput
from agents.report import ReportAgent, ReportInput
from agents.schemas import EvaluationBundle, WorldGenerationInput
from agents.world import WorldAgent
from workers.document_loader import load_document_pair


async def run_pipeline(invoice_path: str, bill_of_lading_path: str, output_dir: str) -> dict:
    """Execute the full agents pipeline and persist JSON/markdown outputs."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for the local pipeline runner.")

    client = AsyncOpenAI(api_key=api_key)
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    agent_kwargs = {"client": client, "model": model}

    documents = load_document_pair(invoice_path=invoice_path, bill_of_lading_path=bill_of_lading_path)

    extraction_agent = ExtractionAgent(**agent_kwargs)
    hs_agent = HSCodeAgent(**agent_kwargs)
    world_agent = WorldAgent(**agent_kwargs)
    compliance_agent = ComplianceAgent(**agent_kwargs)
    duty_agent = DutyAgent(**agent_kwargs)
    debate_agent = DebateAgent(**agent_kwargs)
    meta_agent = MetaAgent(**agent_kwargs)
    output_agent = OutputAgent(**agent_kwargs)
    report_agent = ReportAgent(**agent_kwargs)

    extraction_result = await extraction_agent.run(
        ExtractionInput(
            invoice_text=documents.invoice_text,
            bill_of_lading_text=documents.bill_of_lading_text,
        )
    )
    hs_code_result = await hs_agent.run(HSCodeInput(extraction_result=extraction_result))
    world_result = await world_agent.run(
        WorldGenerationInput(
            hs_code_result=hs_code_result,
            extraction_result=extraction_result,
        )
    )

    async def evaluate_world(world):
        compliance_result, duty_result = await asyncio.gather(
            compliance_agent.run(ComplianceInput(world=world)),
            duty_agent.run(DutyInput(world=world)),
        )
        debate_result = await debate_agent.run(
            DebateInput(
                world=world,
                compliance_result=compliance_result,
                duty_result=duty_result,
            )
        )
        return EvaluationBundle(
            world=world,
            compliance_result=compliance_result,
            duty_result=duty_result,
            debate_result=debate_result,
        )

    evaluations = await asyncio.gather(*(evaluate_world(world) for world in world_result.worlds))
    meta_result = await meta_agent.run(MetaInput(evaluations=list(evaluations)))
    output_result = await output_agent.run(OutputInput(meta_result=meta_result, evaluations=list(evaluations)))
    report_result = await report_agent.run(ReportInput(output_result=output_result))

    target_dir = Path(output_dir).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    json_path = target_dir / "output_result.json"
    report_path = target_dir / report_result.filename_suggestion
    json_path.write_text(json.dumps(output_result.model_dump(mode="json"), indent=2), encoding="utf-8")
    report_path.write_text(report_result.report_markdown, encoding="utf-8")

    return {
        "json_path": str(json_path),
        "report_path": str(report_path),
        "winner_hs_code": output_result.final_hs_code,
        "winning_world_id": str(output_result.winning_world_id),
    }


def parse_args() -> argparse.Namespace:
    """Build the CLI argument parser."""

    parser = argparse.ArgumentParser(description="Run the Customs Brain pipeline locally.")
    parser.add_argument("--invoice", default="tests/fixtures/sample_invoice.txt")
    parser.add_argument("--bill-of-lading", default="tests/fixtures/sample_bill_of_lading.txt")
    parser.add_argument("--output-dir", default="data/local-smoke")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = asyncio.run(
        run_pipeline(
            invoice_path=args.invoice,
            bill_of_lading_path=args.bill_of_lading,
            output_dir=args.output_dir,
        )
    )
    print(json.dumps(result, indent=2))
