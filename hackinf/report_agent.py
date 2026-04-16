from groq import Groq
import os
import json

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_report(invoice, worlds, best_world):

    prompt = f"""
    You are a logistics analyst.

    Given the following shipment data:

    Invoice:
    {json.dumps(invoice, indent=2)}

    Possible Worlds:
    {json.dumps(worlds, indent=2)}

    Selected Best World:
    {json.dumps(best_world, indent=2)}

    Generate a short report with:

    1. Current shipment summary
    2. Comparison of possible worlds
    3. Why the selected world is best
    4. Final recommendation
    
    DO NOT assume country from HS code.
    Use only provided invoice data.
    
    Clarify difference between:
    - Country of origin
    - Selected optimal route country
    Do NOT assume physical shipping route changes.
    Interpret selected world as optimal classification scenario.
    Keep it concise and professional.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content