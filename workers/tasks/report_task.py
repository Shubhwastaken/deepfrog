from agents.report.agent import ReportAgent
async def run_report(ctx: dict) -> dict:
    return await ReportAgent().run(ctx)
