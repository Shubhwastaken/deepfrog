from agents.compliance.agent import ComplianceAgent
async def run_compliance(ctx: dict) -> dict:
    return await ComplianceAgent().run(ctx)
