"""Worker task for API-facing output shaping."""

from agents.output import OutputAgent, OutputInput
from workers.llm import get_agent_kwargs


async def run_output(ctx: dict) -> dict:
    """Flatten final evaluation data into a serializable response payload."""

    agent = OutputAgent(**get_agent_kwargs())
    output_result = await agent.run(
        OutputInput(
            meta_result=ctx["meta_result"],
            evaluations=ctx["evaluations"],
        )
    )
    return {"output_result": output_result}
