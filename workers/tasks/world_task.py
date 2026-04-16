from agents.world_generator.agent import WorldGeneratorAgent
async def run_world_generation(ctx: dict) -> dict:
    return await WorldGeneratorAgent().run(ctx)
