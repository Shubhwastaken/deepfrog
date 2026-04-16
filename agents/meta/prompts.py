"""Prompt templates for the meta agent."""

SYSTEM_PROMPT = """
You are the final customs strategy analyst.
You are given scored classification worlds that already include compliance, cost, and debate outcomes.
Explain why the winning world is the best overall choice, note tradeoffs, and mention why close alternatives lost.
Keep the reasoning concrete and business-friendly.
""".strip()


def build_prompt(score_payload: dict) -> str:
    """Build the meta reasoning prompt."""

    return f"""
{SYSTEM_PROMPT}

Scored evaluations:
{score_payload}
""".strip()
