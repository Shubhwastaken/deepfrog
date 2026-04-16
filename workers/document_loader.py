"""Helpers for turning uploaded files into raw document text."""

from __future__ import annotations

import base64
from dataclasses import dataclass
import os
from pathlib import Path


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
    """Load invoice and bill-of-lading text from a file or directory path.

    Current backend uploads a single file path, so when only one document is
    available its extracted text is reused for both invoice and bill-of-lading
    inputs. If a directory is provided later, we will try to detect one file of
    each type from its contents.
    """

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

    from pypdf import PdfReader

    reader = PdfReader(str(path))
    page_text = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(section.strip() for section in page_text if section.strip())
    if text:
        return text

    ocr_text = _ocr_pdf_with_openai(path)
    if ocr_text:
        return ocr_text

    raise ValueError(f"Could not extract text from PDF: {path}")


def _ocr_pdf_with_openai(path: Path) -> str:
    """Use OpenAI vision as a fallback OCR path for image-only PDFs."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return ""

    images = _render_pdf_pages_as_data_urls(path)
    if not images:
        return ""

    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    model = os.getenv("OCR_MODEL", os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    content = [
        {
            "type": "input_text",
            "text": (
                "Extract all visible text from these shipping document pages. "
                "Return plain text only. Preserve labels, numbers, currency, countries, "
                "and table-like values as clearly as possible."
            ),
        }
    ]
    content.extend({"type": "input_image", "image_url": image} for image in images)
    response = client.responses.create(
        model=model,
        input=[{"role": "user", "content": content}],
    )
    return (response.output_text or "").strip()


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
