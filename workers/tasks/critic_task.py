"""Worker task for deterministic critic evaluation."""

from __future__ import annotations

import asyncio

from agents.critic import CriticAgent
from agents.schemas import DebateInput
from workers.llm import get_optional_agent_kwargs


async def run_critic(ctx: dict) -> dict:
    """Critique every world using compliance, valuation, and duty outputs."""

    agent = CriticAgent(**get_optional_agent_kwargs())
    compliance_by_world = {result.world_id: result for result in ctx["compliance_results"]}
    duty_by_world = {result.world_id: result for result in ctx["duty_results"]}
    valuation_by_world = {result.world_id: result for result in ctx["valuation_results"]}

    critic_results = await asyncio.gather(
        *(
            agent.run(
                DebateInput(
                    world=world,
                    compliance_result=compliance_by_world[world.world_id],
                    duty_result=duty_by_world[world.world_id],
                    valuation_result=valuation_by_world[world.world_id],
                )
            )
            for world in ctx["world_result"].worlds
        )
    )
    return {
        "critic_results": critic_results,
        "debate_results": critic_results,
    }
