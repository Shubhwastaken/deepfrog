from agents.base.base_agent import BaseAgent

class DebateAgent(BaseAgent):
    """Multi-agent debate to resolve HS code ambiguity."""
    def __init__(self):
        super().__init__("DebateAgent")

    async def run(self, input_data: dict) -> dict:
        self.log("Running debate round")
        candidates = input_data.get("hs_codes", [])
        winner = max(candidates, key=lambda x: x.get("confidence", 0)) if candidates else {}
        return {"consensus_hs_code": winner}
