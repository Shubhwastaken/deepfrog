"""Worker task for final world selection."""

from agents.meta import MetaAgent, MetaInput
from workers.llm import get_agent_kwargs


async def run_meta(ctx: dict) -> dict:
    """Score all evaluated worlds and select the winner."""

    agent = MetaAgent(**get_agent_kwargs())
    meta_result = await agent.run(MetaInput(evaluations=ctx["evaluations"]))
    return {"meta_result": meta_result}
