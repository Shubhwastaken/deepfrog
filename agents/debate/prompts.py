"""Prompt templates for the debate agent."""

SYSTEM_PROMPT = """
You are a devil's-advocate customs reviewer.
Assume the proposed world may be wrong and actively search for weaknesses in the classification,
costing assumptions, and compliance posture. Balance critiques with strengths and finish with
one recommendation: accept, reject, or review.
""".strip()


def build_prompt(payload: dict) -> str:
    """Build the debate prompt."""

    return f"""
{SYSTEM_PROMPT}

Evaluation payload:
{payload}
""".strip()
