"""Shared base class for all Customs Brain agents."""

from __future__ import annotations

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

InputModelT = TypeVar("InputModelT", bound=BaseModel)
OutputModelT = TypeVar("OutputModelT", bound=BaseModel)
ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


class LLMCallError(RuntimeError):
    """Raised when the underlying LLM request cannot be parsed successfully."""


class BaseAgent(ABC, Generic[InputModelT, OutputModelT]):
    """Abstract async agent with structured-output LLM helpers."""

    agent_name = "base"

    def __init__(
        self,
        *,
        client: Any,
        model: str,
        logger: logging.Logger | None = None,
        max_retries: int = 3,
        retry_delay_seconds: float = 1.0,
        temperature: float = 0.1,
        request_options: Mapping[str, Any] | None = None,
    ) -> None:
        self.client = client
        self.model = model
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.temperature = temperature
        self.request_options = dict(request_options or {})
        self.logger = logger or logging.getLogger(f"agents.{self.agent_name}")

    @abstractmethod
    async def run(self, input: InputModelT) -> OutputModelT:
        """Execute the agent's business logic."""

    async def call_llm(
        self,
        prompt: str,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        """Call the injected LLM client and parse the response into a model."""

        compiled_prompt = self._build_structured_prompt(prompt, response_model)
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.logger.info("[%s] LLM attempt %s/%s", self.agent_name, attempt, self.max_retries)
                raw_response = await self._invoke_client(compiled_prompt)
                parsed_response = self._parse_response(raw_response, response_model)
                self.logger.info("[%s] LLM response parsed successfully", self.agent_name)
                return parsed_response
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                self.logger.warning(
                    "[%s] LLM attempt %s failed: %s",
                    self.agent_name,
                    attempt,
                    exc,
                )
                if attempt >= self.max_retries:
                    break
                await asyncio.sleep(self.retry_delay_seconds * attempt)

        raise LLMCallError(
            f"{self.agent_name} failed to obtain a valid {response_model.__name__} response"
        ) from last_error

    def _build_structured_prompt(
        self,
        prompt: str,
        response_model: type[BaseModel],
    ) -> str:
        """Append JSON-only schema instructions to an LLM prompt."""

        schema = json.dumps(response_model.model_json_schema(), indent=2, sort_keys=True)
        return (
            f"{prompt.strip()}\n\n"
            "Return JSON only. Do not include markdown fences or commentary.\n"
            "The JSON must validate against this schema:\n"
            f"{schema}"
        )

    async def _invoke_client(self, prompt: str) -> Any:
        """Dispatch a prompt to either OpenAI-, Anthropic-, or callable-style clients."""

        responses_api = getattr(self.client, "responses", None)
        if responses_api and hasattr(responses_api, "create"):
            return await responses_api.create(
                model=self.model,
                input=prompt,
                temperature=self.temperature,
                **self.request_options,
            )

        chat_api = getattr(getattr(self.client, "chat", None), "completions", None)
        if chat_api and hasattr(chat_api, "create"):
            return await chat_api.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                **self.request_options,
            )

        messages_api = getattr(self.client, "messages", None)
        if messages_api and hasattr(messages_api, "create"):
            anthropic_options = dict(self.request_options)
            anthropic_options.setdefault("max_tokens", 2048)
            return await messages_api.create(
                model=self.model,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}],
                **anthropic_options,
            )

        if callable(self.client):
            return await self.client(
                prompt=prompt,
                model=self.model,
                temperature=self.temperature,
                **self.request_options,
            )

        raise TypeError(
            "Unsupported LLM client. Expected AsyncOpenAI-style, Anthropic-style, or async callable client."
        )

    def _parse_response(
        self,
        response: Any,
        response_model: type[ResponseModelT],
    ) -> ResponseModelT:
        """Coerce common provider response shapes into a Pydantic model."""

        if isinstance(response, response_model):
            return response

        if self._looks_like_llm_response(response):
            raw_text = self._extract_text(response)
            try:
                return response_model.model_validate_json(raw_text)
            except ValidationError:
                payload = json.loads(self._extract_json(raw_text))
                return response_model.model_validate(payload)

        if isinstance(response, BaseModel):
            return response_model.model_validate(response.model_dump())

        if isinstance(response, Mapping):
            return response_model.model_validate(dict(response))

        raw_text = self._extract_text(response)
        try:
            return response_model.model_validate_json(raw_text)
        except ValidationError:
            payload = json.loads(self._extract_json(raw_text))
            return response_model.model_validate(payload)

    def _looks_like_llm_response(self, response: Any) -> bool:
        """Detect provider response wrappers that still need text extraction."""

        return any(
            hasattr(response, attribute)
            for attribute in ("output_text", "choices", "content", "output")
        )

    def _extract_text(self, response: Any) -> str:
        """Extract a plain-text payload from common SDK response objects."""

        if isinstance(response, str):
            return response

        if hasattr(response, "output_text") and getattr(response, "output_text"):
            return str(response.output_text)

        if hasattr(response, "content") and isinstance(response.content, list):
            parts: list[str] = []
            for item in response.content:
                text_value = getattr(item, "text", None)
                if text_value:
                    parts.append(str(text_value))
            if parts:
                return "\n".join(parts)

        choices = getattr(response, "choices", None)
        if choices:
            message = getattr(choices[0], "message", None)
            if message is not None:
                parsed = getattr(message, "parsed", None)
                if parsed is not None:
                    if isinstance(parsed, BaseModel):
                        return parsed.model_dump_json()
                    return json.dumps(parsed)

                content = getattr(message, "content", None)
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts: list[str] = []
                    for item in content:
                        if isinstance(item, str):
                            parts.append(item)
                        else:
                            text_value = getattr(item, "text", None)
                            if text_value:
                                parts.append(str(text_value))
                    if parts:
                        return "\n".join(parts)

        if hasattr(response, "model_dump_json"):
            return response.model_dump_json()

        if hasattr(response, "model_dump"):
            return json.dumps(response.model_dump())

        raise TypeError(f"Could not extract text from response type {type(response)!r}")

    def _extract_json(self, text: str) -> str:
        """Recover the first JSON object or array from a text response."""

        candidate = text.strip()
        if candidate.startswith("```"):
            lines = candidate.splitlines()
            if len(lines) >= 3:
                candidate = "\n".join(lines[1:-1]).strip()

        start_object = candidate.find("{")
        start_array = candidate.find("[")
        start_candidates = [index for index in (start_object, start_array) if index != -1]
        if not start_candidates:
            return candidate

        start = min(start_candidates)
        end_object = candidate.rfind("}")
        end_array = candidate.rfind("]")
        end = max(end_object, end_array)
        if end == -1 or end < start:
            return candidate[start:]
        return candidate[start : end + 1]
