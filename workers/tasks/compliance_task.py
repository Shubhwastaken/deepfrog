"""Worker task for compliance evaluation."""

from __future__ import annotations

import asyncio

from agents.compliance import ComplianceAgent, ComplianceInput
from workers.llm import get_agent_kwargs


async def run_compliance(ctx: dict) -> dict:
    """Evaluate every generated world for compliance in parallel."""

    agent = ComplianceAgent(**get_agent_kwargs())
    compliance_results = await asyncio.gather(
        *(agent.run(ComplianceInput(world=world)) for world in ctx["world_result"].worlds)
    )
    return {"compliance_results": compliance_results}
