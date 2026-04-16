"""Worker task for deterministic valuation screening."""

from __future__ import annotations

import asyncio

from agents.valuation import ValuationAgent, ValuationInput


async def run_valuation(ctx: dict) -> dict:
    """Screen every generated world for valuation anomalies in parallel."""

    agent = ValuationAgent()
    valuation_results = await asyncio.gather(
        *(agent.run(ValuationInput(world=world)) for world in ctx["world_result"].worlds)
    )
    return {"valuation_results": valuation_results}
