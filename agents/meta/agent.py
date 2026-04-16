from agents.base.base_agent import BaseAgent
from agents.meta.scorer import MetaScorer

class MetaAgent(BaseAgent):
    def __init__(self):
        super().__init__("MetaAgent")
        self.scorer = MetaScorer()

    async def run(self, input_data: dict) -> dict:
        self.log("Meta scoring")
        return {"meta_score": self.scorer.score(input_data)}
