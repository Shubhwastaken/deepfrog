"""Document extraction agent."""

from __future__ import annotations

from agents.base.base_agent import BaseAgent
from agents.extraction.parser import DocumentParser
from agents.extraction.prompts import build_prompt
from agents.schemas import ExtractionInput, ExtractionResult


class ExtractionAgent(BaseAgent[ExtractionInput, ExtractionResult]):
    """Extract normalized customs facts from invoice and bill-of-lading text."""

    agent_name = "extraction"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.parser = DocumentParser()

    async def run(self, input: ExtractionInput) -> ExtractionResult:
        """Parse source documents into a structured extraction result."""

        validated_input = ExtractionInput.model_validate(input)
        prompt = build_prompt(
            invoice_text=validated_input.invoice_text,
            bill_of_lading_text=validated_input.bill_of_lading_text,
        )
        try:
            result = await self.call_llm(prompt, ExtractionResult)
            return ExtractionResult.model_validate(result.model_dump())
        except Exception as exc:  # noqa: BLE001
            self.logger.warning(
                "[%s] Falling back to deterministic extraction parser after LLM failure: %s",
                self.agent_name,
                exc,
            )
            return self.parser.parse(
                invoice_text=validated_input.invoice_text,
                bill_of_lading_text=validated_input.bill_of_lading_text,
            )
