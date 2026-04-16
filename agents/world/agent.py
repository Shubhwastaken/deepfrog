"""World generation agent."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.schemas import World, WorldGenerationInput, WorldGenerationResult


class WorldAgent(BaseAgent[WorldGenerationInput, WorldGenerationResult]):
    """Create one deterministic world for each HS code candidate."""

    agent_name = "world"

    async def run(self, input: WorldGenerationInput) -> WorldGenerationResult:
        """Convert ranked HS candidates into stable world objects."""

        validated_input = WorldGenerationInput.model_validate(input)
        ordered_candidates = sorted(
            validated_input.hs_code_result.candidates,
            key=lambda candidate: candidate.confidence_score,
            reverse=True,
        )

        worlds = []
        for index, candidate in enumerate(ordered_candidates):
            label = f"World {chr(65 + index)}"
            worlds.append(
                World(
                    hs_code=candidate.hs_code,
                    confidence_score=candidate.confidence_score,
                    extraction_data=validated_input.extraction_result,
                    label=label,
                )
            )

        return WorldGenerationResult.model_validate({"worlds": [world.model_dump(mode="json") for world in worlds]})
