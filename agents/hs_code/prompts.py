"""Prompt templates for the HS code classification agent."""

SYSTEM_PROMPT = """
You are a customs classification specialist.
Based on the extracted shipment facts, propose 2 to 4 plausible 6-digit HS code candidates.
Rank them from most likely to least likely and keep confidence scores calibrated between 0 and 1.
Reasoning should cite classification clues and ambiguities, not generic statements.
""".strip()


def build_prompt(extraction_payload: dict) -> str:
    """Build the HS classification prompt."""

    return f"""
{SYSTEM_PROMPT}

Extraction payload:
{extraction_payload}
""".strip()
