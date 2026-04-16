import re


def extract_total_from_text(text):
    match = re.search(r"TOTAL VALUE[:\s]*([\d,]+\.\d+)", text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def extract_country_from_text(text):
    import re

    matches = re.findall(r"Country:\s*([A-Za-z ]+)", text)

    for m in matches:
        cleaned = m.strip()

        if "United States" in cleaned:
            return "United States"

    for m in matches:
        if "Canada" in m:
            return "Canada"

    return None


def clean_product_summary(text):
    if not text:
        return text

    # remove OCR junk like '5 160 PCS or /6 80
    text = re.sub(r"[\'/]\d+\s*\d*", "", text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def validate_invoice(invoice, raw_text):
    issues = []
    assumptions = []

    # -----------------------------
    # 1. TOTAL VALUE CORRECTION
    # -----------------------------
    actual_total = extract_total_from_text(raw_text)

    if actual_total:
        if invoice.get("total_value") != actual_total:
            invoice["total_value"] = actual_total
            issues.append("Corrected total value from OCR")

    # -----------------------------
    # 2. COUNTRY CORRECTION (NEW 🔥)
    # -----------------------------
    actual_country = extract_country_from_text(raw_text)

    if actual_country:
        if invoice.get("country_of_origin") != actual_country:
            invoice["country_of_origin"] = actual_country
            issues.append("Corrected country from OCR")

    # -----------------------------
    # 3. CURRENCY LOGIC
    # -----------------------------
    extracted_currency = invoice.get("currency")
    origin = invoice.get("country_of_origin")

    if extracted_currency:
        if origin == "United States" and extracted_currency != "USD":
            issues.append("Currency differs from expected for origin country")
    else:
        if origin == "United States":
            invoice["currency"] = "USD"
            assumptions.append("Currency inferred from origin country")

    # -----------------------------
    # 4. QUANTITY SANITY CHECK (NEW 🔥)
    # -----------------------------
    qty = invoice.get("total_quantity")

    if qty:
        try:
            qty = float(qty)
            if qty > 500:   # unrealistic threshold
                invoice["total_quantity"] = None
                issues.append("Invalid total quantity removed")
        except:
            invoice["total_quantity"] = None

    # -----------------------------
    # 5. PRODUCT CLEANUP (NEW 🔥)
    # -----------------------------
    if invoice.get("products_summary"):
        invoice["products_summary"] = clean_product_summary(
            invoice["products_summary"]
        )

    return invoice, issues, assumptions

