from agents.hs_code.agent import HSCodeAgent
async def run_hs_classification(ctx: dict) -> dict:
    return await HSCodeAgent().run(ctx)
