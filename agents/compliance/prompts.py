"""Prompt templates for the compliance agent fallback path."""

SYSTEM_PROMPT = """
You are a customs compliance analyst.
Assess whether the proposed classification world is compliant for the shipment destination.
Be conservative: flag missing information, licensing concerns, sanctions concerns, and any ambiguity that warrants review.
""".strip()


def build_prompt(world_payload: dict) -> str:
    """Build the compliance fallback prompt."""

    return f"""
{SYSTEM_PROMPT}

World payload:
{world_payload}
""".strip()
