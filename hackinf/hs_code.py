import re
from groq import Groq
import os
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def extract_or_predict_hs(raw_text, invoice):

    # Try extracting from raw OCR
    hs_codes = list(set(re.findall(r"\b\d{4}\.\d{2}\b", raw_text)))

    if hs_codes:
        return {
            "method": "extracted",
            "hs_code": hs_codes[0],
            "all_hs_codes": hs_codes,
            "confidence": "high"
        }

    # Fallback LLM
    prompt = f"""
    Predict HS code for:
    {invoice.get("products_summary")}

    Return JSON:
    {{
      "hs_code": "",
      "confidence": ""
    }}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(response.choices[0].message.content)
    except:
        return {"hs_code": "6204", "confidence": "low"}