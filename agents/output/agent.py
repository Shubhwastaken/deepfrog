from agents.base.base_agent import BaseAgent
from agents.output.formatter import OutputFormatter

class OutputAgent(BaseAgent):
    def __init__(self):
        super().__init__("OutputAgent")
        self.formatter = OutputFormatter()

    async def run(self, input_data: dict) -> dict:
        self.log("Formatting final output")
        return self.formatter.format(input_data)
