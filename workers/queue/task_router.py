"""Task router for the Customs Brain worker pipeline."""

from __future__ import annotations

from agents.schemas import EvaluationBundle
from shared.utils.logger import get_logger
from workers.tasks.compliance_task import run_compliance
from workers.tasks.critic_task import run_critic
from workers.tasks.duty_task import run_duty
from workers.tasks.extraction_task import run_extraction
from workers.tasks.hs_task import run_hs_classification
from workers.tasks.meta_task import run_meta
from workers.tasks.output_task import run_output
from workers.tasks.report_task import run_report
from workers.tasks.valuation_task import run_valuation
from workers.tasks.world_task import run_world_generation

logger = get_logger("customs_brain.task_router")


async def route_task(job_id: str, document_paths: dict[str, str] | str):
    """Run the full agent pipeline for a queued job."""

    document_paths = (
        document_paths
        if isinstance(document_paths, dict)
        else {"invoice": document_paths, "bill_of_lading": document_paths}
    )
    ctx = {"job_id": job_id, "document_paths": document_paths}
    ctx.update(await run_extraction(ctx))
    ctx.update(await run_hs_classification(ctx))
    ctx.update(await run_world_generation(ctx))
    ctx.update(await run_compliance(ctx))
    ctx.update(await run_valuation(ctx))
    ctx.update(await run_duty(ctx))
    ctx.update(await run_critic(ctx))
    ctx["evaluations"] = [
        EvaluationBundle(
            world=world,
            compliance_result=next(
                result for result in ctx["compliance_results"] if result.world_id == world.world_id
            ),
            valuation_result=next(
                result for result in ctx["valuation_results"] if result.world_id == world.world_id
            ),
            duty_result=next(
                result for result in ctx["duty_results"] if result.world_id == world.world_id
            ),
            debate_result=next(
                result for result in ctx["debate_results"] if result.world_id == world.world_id
            ),
            critic_result=next(
                result for result in ctx["critic_results"] if result.world_id == world.world_id
            ),
        )
        for world in ctx["world_result"].worlds
    ]
    ctx.update(await run_meta(ctx))
    ctx.update(await run_output(ctx))
    ctx.update(await run_report(ctx))
    logger.info("Pipeline completed for job with report_path=%s", ctx.get("report_path"))
    return {
        "job_id": ctx["job_id"],
        "document_paths": ctx["document_paths"],
        "output_result": ctx["output_result"].model_dump(mode="json"),
        "report_result": ctx["report_result"].model_dump(mode="json"),
        "report_path": ctx["report_path"],
    }
