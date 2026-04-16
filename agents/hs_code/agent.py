from agents.base.base_agent import BaseAgent
from agents.hs_code.classifier import HSClassifier

class HSCodeAgent(BaseAgent):
    def __init__(self):
        super().__init__("HSCodeAgent")
        self.classifier = HSClassifier()

    async def run(self, input_data: dict) -> dict:
        self.log("Classifying HS codes")
        description = input_data.get("extracted", {}).get("fields", {}).get("goods_description", "")
        return {"hs_codes": self.classifier.classify(description)}
