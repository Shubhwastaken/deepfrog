from agents.duty.agent import DutyAgent
async def run_duty(ctx: dict) -> dict:
    return await DutyAgent().run(ctx)
