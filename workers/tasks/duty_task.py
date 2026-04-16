"""Worker task for duty estimation."""

from __future__ import annotations

import asyncio

from agents.duty import DutyAgent, DutyInput
from workers.llm import get_agent_kwargs


async def run_duty(ctx: dict) -> dict:
    """Estimate landed cost for every generated world in parallel."""

    agent = DutyAgent(**get_agent_kwargs())
    duty_results = await asyncio.gather(
        *(agent.run(DutyInput(world=world)) for world in ctx["world_result"].worlds)
    )
    return {"duty_results": duty_results}
