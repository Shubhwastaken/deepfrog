"""Debate agent for adversarial world review."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.debate.prompts import build_prompt
from agents.schemas import DebateInput, DebateResult


class DebateAgent(BaseAgent[DebateInput, DebateResult]):
    """Stress-test a world by asking what could be wrong with it."""

    agent_name = "debate"

    async def run(self, input: DebateInput) -> DebateResult:
        """Return a risk-weighted critique of the proposed world."""

        validated_input = DebateInput.model_validate(input)
        payload = validated_input.model_dump(mode="json")
        prompt = build_prompt(payload)
        result = await self.call_llm(prompt, DebateResult)
        normalized_payload = result.model_dump(mode="json")
        normalized_payload["world_id"] = validated_input.world.world_id
        return DebateResult.model_validate(normalized_payload)
