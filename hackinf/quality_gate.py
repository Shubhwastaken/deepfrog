# quality_gate.py

def check_extraction_quality(invoice, bol):
    issues = []

    # Count non-null fields
    invoice_fields = [
        invoice.get("exporter"),
        invoice.get("importer"),
        invoice.get("products_summary"),
        invoice.get("total_value"),
        invoice.get("country_of_origin"),
    ]

    bol_fields = [
        bol.get("shipper"),
        bol.get("consignee"),
        bol.get("goods_description"),
        bol.get("packages"),
    ]

    invoice_score = sum([1 for x in invoice_fields if x])
    bol_score = sum([1 for x in bol_fields if x])

    # Thresholds (tune if needed)
    if invoice_score < 3:
        issues.append("Low confidence in invoice extraction")

    if bol_score < 2:
        issues.append("Low confidence in BoL extraction")

    status = "fail" if issues else "pass"

    return {
        "status": status,
        "issues": issues,
        "invoice_score": invoice_score,
        "bol_score": bol_score
    }