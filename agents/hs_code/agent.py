"""HS code candidate generation agent."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.hs_code.prompts import build_prompt
from agents.schemas import HSCodeCandidate, HSCodeInput, HSCodeResult


class HSCodeAgent(BaseAgent[HSCodeInput, HSCodeResult]):
    """Generate ranked HS code candidates from extracted shipment facts."""

    agent_name = "hs_code"

    async def run(self, input: HSCodeInput) -> HSCodeResult:
        """Return 2 to 4 ranked HS candidates for the extracted product."""

        validated_input = HSCodeInput.model_validate(input)
        prompt = build_prompt(validated_input.extraction_result.model_dump(mode="json"))
        result = await self.call_llm(prompt, HSCodeResult)
        ranked_candidates = sorted(
            (
                HSCodeCandidate.model_validate(candidate)
                for candidate in result.candidates
            ),
            key=lambda candidate: candidate.confidence_score,
            reverse=True,
        )
        return HSCodeResult.model_validate({"candidates": [candidate.model_dump() for candidate in ranked_candidates]})
