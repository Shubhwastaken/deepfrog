from workers.tasks.extraction_task import run_extraction
from workers.tasks.hs_task import run_hs_classification
from workers.tasks.world_task import run_world_generation
from workers.tasks.compliance_task import run_compliance
from workers.tasks.duty_task import run_duty
from workers.tasks.meta_task import run_meta
from workers.tasks.report_task import run_report

async def route_task(job_id: str, file_path: str):
    ctx = {"job_id": job_id, "file_path": file_path}
    ctx.update(await run_extraction(ctx))
    ctx.update(await run_hs_classification(ctx))
    ctx.update(await run_world_generation(ctx))
    ctx.update(await run_compliance(ctx))
    ctx.update(await run_duty(ctx))
    ctx.update(await run_meta(ctx))
    ctx.update(await run_report(ctx))
    print(f"Job {job_id} complete — report: {ctx.get('report_path')}")
    return ctx
