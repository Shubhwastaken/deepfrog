from agents.base.base_agent import BaseAgent
from agents.report.pdf_generator import PDFGenerator

class ReportAgent(BaseAgent):
    def __init__(self):
        super().__init__("ReportAgent")
        self.generator = PDFGenerator()

    async def run(self, input_data: dict) -> dict:
        self.log("Generating PDF report")
        return {"report_path": self.generator.generate(input_data)}
