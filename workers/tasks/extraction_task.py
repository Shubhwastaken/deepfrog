"""Worker task for document extraction."""

from agents.extraction import ExtractionAgent, ExtractionInput
from workers.document_loader import load_document_pair
from workers.llm import get_agent_kwargs


async def run_extraction(ctx: dict) -> dict:
    """Load uploaded documents and extract normalized customs fields."""

    document_paths = ctx["document_paths"]
    documents = load_document_pair(
        invoice_path=document_paths["invoice"],
        bill_of_lading_path=document_paths["bill_of_lading"],
    )
    agent = ExtractionAgent(**get_agent_kwargs())
    extraction_result = await agent.run(
        ExtractionInput(
            invoice_text=documents.invoice_text,
            bill_of_lading_text=documents.bill_of_lading_text,
        )
    )
    return {
        "invoice_text": documents.invoice_text,
        "bill_of_lading_text": documents.bill_of_lading_text,
        "extraction_result": extraction_result,
    }
