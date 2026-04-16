from agents.base.base_agent import BaseAgent
from agents.extraction.parser import DocumentParser

class ExtractionAgent(BaseAgent):
    def __init__(self):
        super().__init__("ExtractionAgent")
        self.parser = DocumentParser()

    async def run(self, input_data: dict) -> dict:
        self.log("Starting document extraction")
        raw_text = self.parser.extract_text(input_data.get("file_path", ""))
        return {"extracted": self.parser.structure(raw_text)}
