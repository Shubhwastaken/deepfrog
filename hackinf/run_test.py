import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))

from extraction import extract_text
from llm_extractor import process_documents

INVOICE = r"C:\Users\Ankit\OneDrive\Desktop\Commercial-Invoice-Template-Word-Docs-02.pdf"
BOL     = r"C:\Users\Ankit\OneDrive\Desktop\_BILL OF LADING.pdf"

print("=" * 60)
print("[1/2] Extracting Invoice text via OCR...")
invoice_text = extract_text(INVOICE)
print(f"  >> Extracted {len(invoice_text)} chars")

print("[2/2] Extracting Bill of Lading text via OCR...")
bol_text = extract_text(BOL)
print(f"  >> Extracted {len(bol_text)} chars")

print("\nRunning AI pipeline (LLM extraction + compliance + HS Code)...")
result = process_documents(invoice_text, bol_text)

print("\n" + "=" * 60)
print("         FINAL STRUCTURED OUTPUT")
print("=" * 60)
print(json.dumps(result, indent=2, ensure_ascii=False))
