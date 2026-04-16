"""Meta agent that selects the best overall world."""

from __future__ import annotations

from pydantic import Field

from agents.base.base_agent import BaseAgent
from agents.meta.prompts import build_prompt
from agents.meta.scorer import calculate_scores, rank_world_ids
from agents.schemas import CustomsBrainModel, MetaInput, MetaResult


class MetaReasoningPayload(CustomsBrainModel):
    """LLM payload for explaining the scorer's decision."""

    reasoning: str = Field(..., min_length=1)


class MetaAgent(BaseAgent[MetaInput, MetaResult]):
    """Select the winning world using configurable weighted scoring."""

    agent_name = "meta"

    async def run(self, input: MetaInput) -> MetaResult:
        """Rank evaluated worlds and explain the final selection."""

        validated_input = MetaInput.model_validate(input)
        score_breakdown = calculate_scores(
            evaluations=validated_input.evaluations,
            scoring_config=validated_input.scoring_config,
        )
        ranked_world_ids = rank_world_ids(score_breakdown)
        bundle_by_id = {
            str(bundle.world.world_id): bundle
            for bundle in validated_input.evaluations
        }
        winning_world_id = ranked_world_ids[0]
        winning_bundle = bundle_by_id[winning_world_id]

        prompt_payload = {
            "score_breakdown": score_breakdown,
            "winning_world_id": winning_world_id,
            "evaluations": [bundle.model_dump(mode="json") for bundle in validated_input.evaluations],
        }
        reasoning_payload = await self.call_llm(build_prompt(prompt_payload), MetaReasoningPayload)

        return MetaResult(
            winning_world_id=winning_bundle.world.world_id,
            final_hs_code=winning_bundle.world.hs_code,
            score_breakdown=score_breakdown,
            reasoning=reasoning_payload.reasoning,
            alternatives=[bundle_by_id[world_id].world.world_id for world_id in ranked_world_ids[1:]],
        )
