"""Worker task for HS code classification."""

from agents.hs_code import HSCodeAgent, HSCodeInput
from workers.llm import get_agent_kwargs


async def run_hs_classification(ctx: dict) -> dict:
    """Generate ranked HS code candidates from extracted shipment facts."""

    agent = HSCodeAgent(**get_agent_kwargs())
    hs_code_result = await agent.run(
        HSCodeInput(extraction_result=ctx["extraction_result"])
    )
    return {"hs_code_result": hs_code_result}
