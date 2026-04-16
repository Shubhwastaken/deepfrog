"""Worker task for deterministic world generation."""

from agents.schemas import WorldGenerationInput
from agents.world import WorldAgent
from workers.llm import get_agent_kwargs


async def run_world_generation(ctx: dict) -> dict:
    """Create one world per HS code candidate."""

    agent = WorldAgent(**get_agent_kwargs())
    world_result = await agent.run(
        WorldGenerationInput(
            hs_code_result=ctx["hs_code_result"],
            extraction_result=ctx["extraction_result"],
        )
    )
    return {"world_result": world_result}
