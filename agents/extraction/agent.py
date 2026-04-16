"""Document extraction agent."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.extraction.prompts import build_prompt
from agents.schemas import ExtractionInput, ExtractionResult


class ExtractionAgent(BaseAgent[ExtractionInput, ExtractionResult]):
    """Extract normalized customs facts from invoice and bill-of-lading text."""

    agent_name = "extraction"

    async def run(self, input: ExtractionInput) -> ExtractionResult:
        """Parse source documents into a structured extraction result."""

        validated_input = ExtractionInput.model_validate(input)
        prompt = build_prompt(
            invoice_text=validated_input.invoice_text,
            bill_of_lading_text=validated_input.bill_of_lading_text,
        )
        result = await self.call_llm(prompt, ExtractionResult)
        return ExtractionResult.model_validate(result.model_dump())
