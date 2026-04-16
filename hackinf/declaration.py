def generate_declaration(invoice, compliance, hs, assumptions):

    return {
        "product": invoice.get("products_summary"),
        "hs_code": hs.get("hs_code"),
        "value": invoice.get("total_value"),
        "currency": invoice.get("currency"),
        "origin": invoice.get("country_of_origin"),
        "status": "approved" if compliance["status"] == "pass" else "warning",
        "remarks": compliance.get("issues"),
        "assumptions": assumptions
    }