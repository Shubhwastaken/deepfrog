from pathlib import Path

from workers import document_loader


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": "Invoice Number: INV-1001\nCountry of Origin: India",
                    }
                }
            ]
        }


def test_ocr_pdf_with_github_models_uses_multimodal_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured["url"] = url
        captured["headers"] = headers
        captured["json"] = json
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr(document_loader.httpx, "post", fake_post)

    result = document_loader._ocr_pdf_with_github_models(
        Path("sample.pdf"),
        ["data:image/png;base64,abc123"],
        api_key="github-pat",
    )

    assert "Invoice Number: INV-1001" in result
    assert captured["url"] == "https://models.github.ai/inference/chat/completions"
    assert captured["headers"]["Authorization"] == "Bearer github-pat"
    assert captured["json"]["model"] == "openai/gpt-4.1"
    assert captured["json"]["messages"][0]["content"][0]["type"] == "text"
    assert captured["json"]["messages"][0]["content"][1]["type"] == "image_url"
    assert captured["timeout"].write == 180
