def check_compliance(invoice, comparison):
    issues = []

    issues.extend(comparison["issues"])

    # Required fields
    required = ["exporter", "importer", "total_value"]

    for field in required:
        if not invoice.get(field):
            issues.append(f"Missing {field}")

    # Currency inference
    if not invoice.get("currency"):
        if invoice.get("country_of_origin") == "United States":
            invoice["currency"] = "USD"

    # Value sanity
    if invoice.get("total_value") and invoice["total_value"] <= 0:
        issues.append("Invalid value")

    return {
        "status": "pass" if not issues else "warning",
        "issues": issues
    }