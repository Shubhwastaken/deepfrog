from groq import Groq
import json
import re
import os

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# -----------------------------
# SAFE JSON PARSER (ROBUST)
# -----------------------------
def extract_json(text):
    if not text:
        return None

    # Remove markdown
    text = text.replace("```json", "").replace("```", "").strip()

    # 1. Try direct parse
    try:
        return json.loads(text)
    except:
        pass

    # 2. Extract JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        candidate = match.group()

        try:
            return json.loads(candidate)
        except:
            pass

        # 3. Fix common JSON issues
        try:
            candidate = re.sub(r",\s*}", "}", candidate)
            candidate = re.sub(r",\s*]", "]", candidate)
            return json.loads(candidate)
        except:
            pass

    return None


# -----------------------------
# MAIN EXTRACTION FUNCTION
# -----------------------------
def extract_all(invoice_text, bol_text, retries=2):

    prompt = f"""
    Extract structured data from BOTH documents.

    Return STRICT JSON only.
    - No explanation
    - No markdown
    - No trailing text

    {{
      "invoice": {{
        "exporter": "",
        "importer": "",
        "products_summary": "",
        "total_quantity": null,
        "total_value": null,
        "currency": "",
        "country_of_origin": ""
      }},
      "bol": {{
        "shipper": "",
        "consignee": "",
        "goods_description": "",
        "packages": null,
        "weight": null
      }}
    }}

    Rules:
    - Do NOT hallucinate
    - Do NOT confuse packages with quantity
    - If currency not explicitly present, infer from country if possible

    INVOICE:
    {invoice_text[:1500]}

    BOL:
    {bol_text[:1500]}
    """

    for attempt in range(retries + 1):

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content

        print(f"\n--- RAW LLM OUTPUT (Attempt {attempt+1}) ---\n")
        print(raw)

        parsed = extract_json(raw)

        if parsed is not None:
            return parsed

        print("⚠️ JSON parsing failed, retrying...")

    # -----------------------------
    # FINAL FALLBACK (SAFE STRUCTURE)
    # -----------------------------
    print("❌ All attempts failed. Returning safe fallback.")

    return {
        "invoice": {
            "exporter": None,
            "importer": None,
            "products_summary": None,
            "total_quantity": None,
            "total_value": None,
            "currency": None,
            "country_of_origin": None
        },
        "bol": {
            "shipper": None,
            "consignee": None,
            "goods_description": None,
            "packages": None,
            "weight": None
        }
    }