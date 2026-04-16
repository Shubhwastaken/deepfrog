from extraction import extract_text
from llm_extractor import extract_all
from Comparator import compare_documents
from compliance import check_compliance
from hs_code import extract_or_predict_hs
from declaration import generate_declaration
import json
from validator import validate_invoice
from world import generate_worlds, select_best_world
from report_agent import generate_report
from quality_gate import check_extraction_quality

invoice_path = r"C:\Users\shshv\PycharmProjects\hackinf\images\Commercial-Invoice-Template-Word-Docs-02.jpg"
bol_path = r"C:\Users\shshv\PycharmProjects\hackinf\images\_BILL OF LADING.pdf"

invoice_raw = extract_text(invoice_path)
bol_raw = extract_text(bol_path)

data = extract_all(invoice_raw, bol_raw)

data = extract_all(invoice_raw, bol_raw)

invoice = data["invoice"]
bol = data["bol"]

# ✅ NEW: QUALITY CHECK
quality = check_extraction_quality(invoice, bol)

if quality["status"] == "fail":
    result = {
        "status": "failed",
        "reason": "Extraction quality too low",
        "details": quality
    }

    print(result)


invoice = data["invoice"]
bol = data["bol"]

# ✅ NEW STEP: VALIDATION
invoice, validation_issues, assumptions = validate_invoice(invoice, invoice_raw)
comparison = compare_documents(invoice, bol)
compliance = check_compliance(invoice, comparison)

# Merge validation issues into compliance
compliance["issues"].extend(validation_issues)

hs = extract_or_predict_hs(invoice_raw, invoice)

worlds = generate_worlds(invoice, hs)
best_world = select_best_world(worlds)
selected_hs = best_world["hs_code"] if best_world else hs.get("hs_code")

hs_override = {
    "hs_code": selected_hs
}

declaration = generate_declaration(invoice, compliance, hs_override, assumptions)

report = generate_report(invoice, worlds, best_world)
result = {
    "invoice": invoice,
    "bol": bol,
    "comparison": comparison,
    "compliance": compliance,
    "hs_code": hs,
    "worlds": worlds,
    "selected_world": best_world,
    "declaration": declaration,
    "report": report
}

print(json.dumps(result, indent=2))