"""World generation agent."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.schemas import WorldGenerationInput, WorldGenerationResult
from agents.world.builder import WorldBuilder


class WorldAgent(BaseAgent[WorldGenerationInput, WorldGenerationResult]):
    """Create deterministic, context-rich worlds from HS candidates."""

    agent_name = "world"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.builder = WorldBuilder()

    async def run(self, input: WorldGenerationInput) -> WorldGenerationResult:
        """Convert ranked HS candidates into stable world objects."""

        validated_input = WorldGenerationInput.model_validate(input)
        worlds = self.builder.build(
            validated_input.extraction_result,
            validated_input.hs_code_result.candidates,
        )
        return WorldGenerationResult(worlds=worlds)
