"""LLM client bootstrap helpers for worker tasks."""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

import httpx
from shared.config.env_loader import load_project_env


load_project_env(__file__)


@lru_cache(maxsize=1)
def get_llm_client() -> Any:
    """Return a cached async LLM client based on configured API keys."""

    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key:
        from openai import AsyncOpenAI

        return AsyncOpenAI(
            api_key=groq_api_key,
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1"),
            timeout=httpx.Timeout(3600.0),
        )

    xai_api_key = os.getenv("XAI_API_KEY")
    if xai_api_key:
        from openai import AsyncOpenAI

        return AsyncOpenAI(
            api_key=xai_api_key,
            base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
            timeout=httpx.Timeout(3600.0),
        )

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        from openai import AsyncOpenAI

        return AsyncOpenAI(api_key=openai_api_key)

    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        from anthropic import AsyncAnthropic

        return AsyncAnthropic(api_key=anthropic_api_key)

    raise RuntimeError(
        "No LLM API key configured. Set GROQ_API_KEY, XAI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."
    )


def get_model_name() -> str:
    """Resolve the model name for the configured provider."""

    if os.getenv("GROQ_API_KEY"):
        return os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    if os.getenv("XAI_API_KEY"):
        return os.getenv("XAI_MODEL", "grok-4.20-beta-latest-non-reasoning")
    if os.getenv("OPENAI_API_KEY"):
        return os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if os.getenv("ANTHROPIC_API_KEY"):
        return os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-latest")
    raise RuntimeError(
        "No LLM API key configured. Set GROQ_API_KEY, XAI_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY."
    )


def get_agent_kwargs() -> dict[str, Any]:
    """Build constructor kwargs shared by all agent instances."""

    return {
        "client": get_llm_client(),
        "model": get_model_name(),
    }


def get_optional_agent_kwargs() -> dict[str, Any]:
    """Return agent kwargs when an LLM provider is configured, otherwise an empty dict."""

    try:
        return get_agent_kwargs()
    except RuntimeError:
        return {}
