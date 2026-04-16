"""Prompt templates for the duty estimation agent fallback path."""

SYSTEM_PROMPT = """
You are a customs duty analyst.
Estimate duty and indirect tax rates for the proposed HS code and destination country.
Be realistic and conservative, and explain the basis of your estimate succinctly.
""".strip()


def build_prompt(world_payload: dict) -> str:
    """Build the duty fallback prompt."""

    return f"""
{SYSTEM_PROMPT}

World payload:
{world_payload}
""".strip()
