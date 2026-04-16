"""Deterministic extraction helpers used when the LLM path fails."""

from __future__ import annotations

import re
from pathlib import Path

from agents.schemas import ExtractionResult


class DocumentParser:
    """Best-effort parser for invoices and bills of lading."""

    _FIELD_PATTERNS = {
        "hs_code_hint": [
            r"Suggested HS Code:\s*([0-9]{6})",
            r"HS Code(?: Hint)?:\s*([0-9]{6})",
        ],
        "declared_value_usd": [
            r"Total Declared Value:\s*([0-9]+(?:\.[0-9]+)?)\s*USD",
            r"Declared Value:\s*([0-9]+(?:\.[0-9]+)?)\s*USD",
        ],
        "quantity": [
            r"Quantity:\s*([0-9]+(?:\.[0-9]+)?)",
        ],
        "unit": [
            r"Quantity:\s*[0-9]+(?:\.[0-9]+)?\s+([A-Za-z]+)",
        ],
        "origin_country": [
            r"Origin Country:\s*(.+)",
            r"Country of Origin:\s*(.+)",
        ],
        "destination_country": [
            r"Destination Country:\s*(.+)",
            r"Country of Destination:\s*(.+)",
            r"Port of Discharge:.*?,\s*([A-Za-z][A-Za-z ]+)$",
        ],
        "currency": [
            r"Currency:\s*([A-Z]{3})",
        ],
        "incoterms": [
            r"Incoterms:\s*([A-Z]{3})\b",
        ],
    }

    def extract_text(self, file_path: str) -> str:
        """Read text from a file path for legacy tests."""

        try:
            return Path(file_path).read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return Path(file_path).read_text(encoding="latin-1")
        except Exception:
            return ""

    def structure(self, text: str) -> dict:
        """Return a legacy dict representation for compatibility."""

        result = self.parse(invoice_text=text, bill_of_lading_text=text)
        return {"raw_text": text, "fields": result.model_dump(mode="json")}

    def parse(self, *, invoice_text: str, bill_of_lading_text: str) -> ExtractionResult:
        """Combine invoice and bill-of-lading text into a structured payload."""

        invoice_text = invoice_text or ""
        bill_of_lading_text = bill_of_lading_text or ""
        combined_text = "\n".join([invoice_text, bill_of_lading_text]).strip()

        product_description = (
            self._capture_block(invoice_text, "Item Description")
            or self._capture_block(bill_of_lading_text, "Cargo Description")
            or self._capture_inline(combined_text, "Product Description")
            or self._capture_inline(combined_text, "Description")
            or "Unspecified goods"
        )

        payload = {
            "product_description": self._clean_value(product_description),
            "hs_code_hint": self._extract_match(invoice_text, "hs_code_hint"),
            "declared_value_usd": self._extract_float(invoice_text, "declared_value_usd"),
            "quantity": self._extract_float(invoice_text, "quantity"),
            "unit": self._extract_match(invoice_text, "unit"),
            "origin_country": self._extract_match(f"{invoice_text}\n{bill_of_lading_text}", "origin_country"),
            "destination_country": self._normalize_destination_country(
                self._extract_match(f"{invoice_text}\n{bill_of_lading_text}", "destination_country")
            ),
            "currency": self._extract_match(invoice_text, "currency"),
            "incoterms": self._extract_match(invoice_text, "incoterms"),
        }
        return ExtractionResult.model_validate(payload)

    def _extract_match(self, text: str, field_name: str) -> str | None:
        for pattern in self._FIELD_PATTERNS.get(field_name, []):
            match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
            if match:
                return self._clean_value(match.group(1))
        return None

    def _extract_float(self, text: str, field_name: str) -> float | None:
        value = self._extract_match(text, field_name)
        if value is None:
            return None
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None

    def _capture_inline(self, text: str, label: str) -> str | None:
        match = re.search(rf"{re.escape(label)}:\s*(.+)", text, flags=re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    def _capture_block(self, text: str, label: str) -> str | None:
        match = re.search(
            rf"{re.escape(label)}:\s*(.+?)(?:\n\s*\n|\n[A-Z][A-Za-z /-]+:|$)",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            return match.group(1)
        return None

    def _normalize_destination_country(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        aliases = {
            "uae": "United Arab Emirates",
            "u.a.e.": "United Arab Emirates",
        }
        return aliases.get(normalized.lower(), normalized)

    def _clean_value(self, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = re.sub(r"\s+", " ", value).strip(" .,:;\n\t")
        return cleaned or None
