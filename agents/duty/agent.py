from agents.base.base_agent import BaseAgent
from agents.duty.calculator import DutyCalculator

class DutyAgent(BaseAgent):
    def __init__(self):
        super().__init__("DutyAgent")
        self.calculator = DutyCalculator()

    async def run(self, input_data: dict) -> dict:
        self.log("Calculating duties")
        return {"duty_calculation": self.calculator.calculate(input_data)}
