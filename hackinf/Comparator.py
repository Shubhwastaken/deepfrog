def keyword_overlap(a, b):
    if not a or not b:
        return 0

    set_a = set(a.lower().split())
    set_b = set(b.lower().split())

    return len(set_a & set_b) / max(len(set_a), 1)


def compare_documents(invoice, bol):
    issues = []

    if not bol:
        issues.append("BoL missing")

    # Product similarity
    overlap = keyword_overlap(
        invoice.get("products_summary", ""),
        bol.get("goods_description", "")
    )

    if overlap < 0.3:
        issues.append("Product description mismatch")

    # Check key fields
    if not invoice.get("total_value"):
        issues.append("Missing total value")

    if not invoice.get("exporter"):
        issues.append("Missing exporter")

    return {
        "status": "pass" if not issues else "warning",
        "issues": issues
    }