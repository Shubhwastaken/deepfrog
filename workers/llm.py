"""LLM client bootstrap helpers for worker tasks."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any


@lru_cache(maxsize=1)
def get_llm_client() -> Any:
    """Return a cached async LLM client based on configured API keys."""

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=openai_api_key)

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(api_key=anthropic_api_key)

    raise RuntimeError("No LLM API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")


def get_model_name() -> str:
    """Resolve the model name for the configured provider."""

    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if os.getenv("ANTHROPIC_API_KEY"):
        return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    raise RuntimeError("No LLM API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY.")


def get_agent_kwargs() -> dict[str, Any]:
    """Build constructor kwargs shared by all agent instances."""

    return {
        "client": get_llm_client(),
        "model": get_model_name(),
    }
