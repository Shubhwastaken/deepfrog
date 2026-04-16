import pytest
from agents.extraction.parser import DocumentParser

def test_extract_text(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("Invoice #1234 from ACME Corp")
    assert "ACME" in DocumentParser().extract_text(str(f))

def test_structure_returns_dict():
    assert isinstance(DocumentParser().structure("some text"), dict)
