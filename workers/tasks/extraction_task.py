from agents.extraction.agent import ExtractionAgent
async def run_extraction(ctx: dict) -> dict:
    return await ExtractionAgent().run(ctx)
