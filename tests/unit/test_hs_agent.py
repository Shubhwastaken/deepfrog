import pytest
from agents.hs_code.classifier import HSClassifier

def test_classify_returns_list():
    result = HSClassifier().classify("laptop computer")
    assert isinstance(result, list) and len(result) > 0
    assert "code" in result[0] and "confidence" in result[0]
