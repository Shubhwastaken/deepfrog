"""Worker task for adversarial world review."""

from __future__ import annotations

import asyncio

from agents.debate import DebateAgent, DebateInput
from workers.llm import get_agent_kwargs


async def run_debate(ctx: dict) -> dict:
    """Critique every world using its compliance and duty outcomes."""

    agent = DebateAgent(**get_agent_kwargs())
    compliance_by_world = {
        result.world_id: result for result in ctx["compliance_results"]
    }
    duty_by_world = {
        result.world_id: result for result in ctx["duty_results"]
    }

    debate_results = await asyncio.gather(
        *(
            agent.run(
                DebateInput(
                    world=world,
                    compliance_result=compliance_by_world[world.world_id],
                    duty_result=duty_by_world[world.world_id],
                )
            )
            for world in ctx["world_result"].worlds
        )
    )
    return {"debate_results": debate_results}
