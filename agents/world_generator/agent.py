from agents.base.base_agent import BaseAgent
from agents.world_generator.builder import WorldBuilder

class WorldGeneratorAgent(BaseAgent):
    def __init__(self):
        super().__init__("WorldGeneratorAgent")
        self.builder = WorldBuilder()

    async def run(self, input_data: dict) -> dict:
        self.log("Generating trade worlds")
        return {"worlds": self.builder.generate(input_data)}
