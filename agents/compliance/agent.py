from agents.base.base_agent import BaseAgent
from agents.compliance.rules_engine import RulesEngine

class ComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__("ComplianceAgent")
        self.engine = RulesEngine()

    async def run(self, input_data: dict) -> dict:
        self.log("Running compliance checks")
        country = input_data.get("extracted", {}).get("fields", {}).get("destination_country", "")
        return {"compliance_issues": self.engine.check(input_data, country)}
