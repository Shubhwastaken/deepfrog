"""Prompt templates for the extraction agent."""

SYSTEM_PROMPT = """
You extract structured customs data from commercial shipping documents.
Reconcile invoice and bill of lading content into a single best-effort view.
Prefer explicit facts over inference, normalize currencies and incoterms when present,
and leave fields null when the documents do not support a reliable answer.
Declared value must be expressed in USD when possible.
""".strip()


def build_prompt(invoice_text: str, bill_of_lading_text: str) -> str:
    """Build the extraction prompt for the LLM."""

    return f"""
{SYSTEM_PROMPT}

Invoice text:
\"\"\"
{invoice_text}
\"\"\"

Bill of lading text:
\"\"\"
{bill_of_lading_text}
\"\"\"
""".strip()
