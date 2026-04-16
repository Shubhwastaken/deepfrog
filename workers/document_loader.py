"""Helpers for turning uploaded files into raw document text."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import os
from pathlib import Path

import httpx
from openai import OpenAI

from shared.config.env_loader import load_project_env

load_project_env(__file__)


@dataclass(slots=True)
class LoadedDocuments:
    """Raw document text payload consumed by the extraction task."""

    invoice_text: str
    bill_of_lading_text: str
    invoice_path: str
    bill_of_lading_path: str


def load_document_pair(invoice_path: str, bill_of_lading_path: str) -> LoadedDocuments:
    """Load invoice and bill-of-lading text from explicit file paths."""

    invoice_source = Path(invoice_path).expanduser().resolve()
    bill_source = Path(bill_of_lading_path).expanduser().resolve()
    return LoadedDocuments(
        invoice_text=_read_text(invoice_source),
        bill_of_lading_text=_read_text(bill_source),
        invoice_path=str(invoice_source),
        bill_of_lading_path=str(bill_source),
    )


def load_documents(file_path: str) -> LoadedDocuments:
    """Load invoice and bill-of-lading text from a file or directory path."""

    source_path = Path(file_path).expanduser().resolve()
    if source_path.is_dir():
        return _load_from_directory(source_path)

    document_text = _read_text(source_path)
    return LoadedDocuments(
        invoice_text=document_text,
        bill_of_lading_text=document_text,
        invoice_path=str(source_path),
        bill_of_lading_path=str(source_path),
    )


def _load_from_directory(directory: Path) -> LoadedDocuments:
    """Detect invoice and bill-of-lading files inside a directory."""

    files = [path for path in directory.iterdir() if path.is_file()]
    if not files:
        raise FileNotFoundError(f"No files found in upload directory: {directory}")

    invoice_file = _match_file(files, keywords=("invoice", "inv"))
    bill_file = _match_file(files, keywords=("bill", "bol", "lading"))
    fallback_file = files[0]

    invoice_source = invoice_file or fallback_file
    bill_source = bill_file or invoice_source

    return LoadedDocuments(
        invoice_text=_read_text(invoice_source),
        bill_of_lading_text=_read_text(bill_source),
        invoice_path=str(invoice_source),
        bill_of_lading_path=str(bill_source),
    )


def _match_file(files: list[Path], *, keywords: tuple[str, ...]) -> Path | None:
    """Return the first file whose name contains any requested keyword."""

    for file_path in files:
        lowercase_name = file_path.name.lower()
        if any(keyword in lowercase_name for keyword in keywords):
            return file_path
    return None


def _read_text(path: Path) -> str:
    """Read plain text from PDF and text-like files."""

    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _read_pdf(path)

    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")


def _read_pdf(path: Path) -> str:
    """Extract page text from a PDF file."""

    direct_text = _extract_pdf_text_with_pypdf(path)
    if direct_text:
        return direct_text

    fitz_text = _extract_pdf_text_with_fitz(path)
    if fitz_text:
        return fitz_text

    ocr_text = _ocr_pdf(path)
    if ocr_text:
        return ocr_text

    raise ValueError(f"Could not extract text from PDF: {path}")


def _extract_pdf_text_with_pypdf(path: Path) -> str:
    """Try normal text extraction with pypdf first."""

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    page_text = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(section.strip() for section in page_text if section.strip())


def _extract_pdf_text_with_fitz(path: Path) -> str:
    """Try PyMuPDF text extraction as a second pass."""

    import fitz

    document = fitz.open(path)
    try:
        page_text = [page.get_text("text") or "" for page in document]
    finally:
        document.close()
    return "\n".join(section.strip() for section in page_text if section.strip())


def _ocr_pdf(path: Path) -> str:
    """Run OCR against configured multimodal providers."""

    images = _render_pdf_pages_as_data_urls(path)
    if not images:
        return ""

    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        return _ocr_pdf_with_openai_compatible(
            images=images,
            api_key=groq_api_key,
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            model=os.getenv(
                "GROQ_OCR_MODEL",
                os.getenv("OCR_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct"),
            ),
        )

    xai_api_key = os.getenv("XAI_API_KEY")
    if xai_api_key:
        return _ocr_pdf_with_openai_compatible(
            images=images,
            api_key=xai_api_key,
            base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
            model=os.getenv("OCR_MODEL", os.getenv("XAI_OCR_MODEL", os.getenv("XAI_MODEL", "grok-4"))),
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        return _ocr_pdf_with_openai_compatible(
            images=images,
            api_key=openai_api_key,
            base_url=os.getenv("OPENAI_BASE_URL") or None,
            model=os.getenv("OCR_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini")),
        )

    github_api_key = os.getenv("GITHUB_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if github_api_key:
        return _ocr_pdf_with_github_models(path, images, github_api_key)

    return ""


def _ocr_pdf_with_openai_compatible(
    *,
    images: list[str],
    api_key: str,
    model: str,
    base_url: str | None = None,
) -> str:
    """Use an OpenAI-compatible multimodal chat endpoint for OCR."""

    client_kwargs = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = OpenAI(**client_kwargs)
    completion = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": _build_multimodal_content(images)}],
    )
    message_content = completion.choices[0].message.content
    if isinstance(message_content, str):
        return message_content.strip()
    if isinstance(message_content, list):
        text_parts: list[str] = []
        for item in message_content:
            if isinstance(item, str):
                text_parts.append(item)
                continue
            text_value = getattr(item, "text", None)
            if text_value:
                text_parts.append(str(text_value))
        return "\n".join(part.strip() for part in text_parts if part.strip())
    return ""


def _ocr_pdf_with_github_models(path: Path, images: list[str], api_key: str) -> str:
    """Use GitHub Models multimodal chat completions for OCR."""

    response = httpx.post(
        "https://models.github.ai/inference/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("GITHUB_OCR_MODEL", "openai/gpt-4.1"),
            "messages": [
                {
                    "role": "user",
                    "content": _build_multimodal_content(images),
                }
            ],
            "temperature": 0.0,
            "max_tokens": 4096,
        },
        timeout=httpx.Timeout(180.0, connect=30.0, read=180.0, write=180.0),
    )
    response.raise_for_status()
    payload = response.json()
    return (payload["choices"][0]["message"]["content"] or "").strip()


def _build_multimodal_content(images: list[str]) -> list[dict]:
    """Build a provider-compatible OCR prompt with image inputs."""

    content: list[dict] = [
        {
            "type": "text",
            "text": (
                "Extract all visible text from these shipping document pages. "
                "Return plain text only. Preserve labels, numbers, currency, countries, "
                "and table-like values as clearly as possible."
            ),
        }
    ]
    for image in images:
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image,
                    "detail": "high",
                },
            }
        )
    return content


def _render_pdf_pages_as_data_urls(path: Path, max_pages: int = 3) -> list[str]:
    """Render PDF pages to PNG data URLs for OCR fallback."""

    import fitz

    document = fitz.open(path)
    image_urls: list[str] = []
    try:
        for page_index in range(min(len(document), max_pages)):
            page = document.load_page(page_index)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            png_bytes = pixmap.tobytes("png")
            encoded = base64.b64encode(png_bytes).decode("ascii")
            image_urls.append(f"data:image/png;base64,{encoded}")
    finally:
        document.close()
    return image_urls
