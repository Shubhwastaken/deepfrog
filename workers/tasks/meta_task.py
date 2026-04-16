from agents.meta.agent import MetaAgent
async def run_meta(ctx: dict) -> dict:
    return await MetaAgent().run(ctx)
