import asyncio

import pytest

from agents.extraction.agent import ExtractionAgent
from agents.extraction.parser import DocumentParser
from agents.schemas import ExtractionInput


def test_extract_text(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Invoice #1234 from ACME Corp")
    assert "ACME" in DocumentParser().extract_text(str(f))


def test_structure_returns_dict():
    assert isinstance(DocumentParser().structure("some text"), dict)


def test_parser_extracts_structured_fields_from_sample_docs():
    parser = DocumentParser()
    invoice_text = (
        "COMMERCIAL INVOICE\n"
        "Origin Country: India\n"
        "Destination Country: United Arab Emirates\n"
        "Incoterms: CIF Dubai\n"
        "Currency: USD\n"
        "Item Description:\nPortable lithium-ion power banks, 10000mAh, packed for retail sale.\n"
        "Quantity: 250 pieces\n"
        "Total Declared Value: 4500.00 USD\n"
        "Suggested HS Code: 850760\n"
    )
    bill_text = (
        "BILL OF LADING\n"
        "Country of Origin: India\n"
        "Country of Destination: United Arab Emirates\n"
        "Cargo Description:\n250 cartons containing portable lithium-ion power banks for consumer electronics.\n"
    )

    result = parser.parse(invoice_text=invoice_text, bill_of_lading_text=bill_text)

    assert result.product_description.startswith("Portable lithium-ion power banks")
    assert result.hs_code_hint == "850760"
    assert result.declared_value_usd == 4500.0
    assert result.quantity == 250.0
    assert result.unit == "pieces"
    assert result.origin_country == "India"
    assert result.destination_country == "United Arab Emirates"
    assert result.currency == "USD"
    assert result.incoterms == "CIF"


def test_extraction_agent_falls_back_when_llm_fails():
    async def failing_client(**kwargs):
        raise RuntimeError("synthetic llm failure")

    agent = ExtractionAgent(client=failing_client, model="test-model")
    result = asyncio.run(
        agent.run(
            ExtractionInput(
                invoice_text=(
                    "Item Description:\nPortable chargers\n"
                    "Origin Country: India\n"
                    "Destination Country: United Arab Emirates\n"
                    "Quantity: 12 units\n"
                    "Total Declared Value: 240.00 USD\n"
                ),
                bill_of_lading_text="Country of Destination: United Arab Emirates",
            )
        )
    )

    assert result.product_description == "Portable chargers"
    assert result.origin_country == "India"
    assert result.destination_country == "United Arab Emirates"
    assert result.quantity == 12.0
    assert result.declared_value_usd == 240.0
