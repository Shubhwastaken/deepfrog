"""In-process job orchestration for local development mode."""

from __future__ import annotations

import asyncio
import os
import uuid
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

LOCAL_JOBS: dict[str, dict] = {}


def create_local_job(invoice_path: str, bill_of_lading_path: str, owner_email: str) -> dict:
    """Create an in-memory job record for local development mode."""

    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "owner_email": owner_email,
        "status": "queued",
        "document_paths": {
            "invoice": invoice_path,
            "bill_of_lading": bill_of_lading_path,
        },
        "results": None,
        "report_path": None,
        "error_message": None,
    }
    LOCAL_JOBS[job_id] = job
    return job


def get_local_job(job_id: str) -> dict | None:
    """Return a previously created local-mode job."""

    return LOCAL_JOBS.get(job_id)


async def process_local_job(job_id: str) -> None:
    """Run the agent pipeline directly inside the backend process."""

    job = LOCAL_JOBS[job_id]
    job["status"] = "processing"

    try:
      payload = await _run_pipeline(
          invoice_path=job["document_paths"]["invoice"],
          bill_of_lading_path=job["document_paths"]["bill_of_lading"],
      )
    except Exception as exc:  # noqa: BLE001
      job["status"] = "failed"
      job["error_message"] = str(exc)
      return

    job["status"] = "completed"
    job["results"] = payload["output_result"]
    job["report_path"] = payload["report_path"]
    job["error_message"] = None


async def _run_pipeline(invoice_path: str, bill_of_lading_path: str) -> dict:
    """Execute the full agents pipeline and persist local output artifacts."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for LOCAL_PIPELINE_MODE.")

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

    report_dir = Path(os.getenv("REPORT_DIR", "data/reports")).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / report_result.filename_suggestion
    report_path.write_text(report_result.report_markdown, encoding="utf-8")

    return {
        "output_result": output_result.model_dump(mode="json"),
        "report_path": str(report_path),
    }
