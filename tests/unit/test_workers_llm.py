import asyncio

from workers import llm


class _FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "choices": [
                {
                    "message": {
                        "content": '{"status":"ok"}',
                    }
                }
            ]
        }


class _FakeAsyncClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    async def post(self, url: str, json: dict) -> _FakeResponse:
        self.calls.append((url, json))
        return _FakeResponse()


def test_get_agent_kwargs_supports_github_models(monkeypatch):
    llm.get_llm_client.cache_clear()
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("GITHUB_MODELS_TOKEN", "github-pat")
    monkeypatch.setenv("GITHUB_MODEL", "openai/gpt-5-nano")

    agent_kwargs = llm.get_agent_kwargs()

    assert isinstance(agent_kwargs["client"], llm.GitHubModelsClient)
    assert agent_kwargs["model"] == "openai/gpt-5-nano"


def test_github_models_client_posts_chat_completion_payload():
    client = llm.GitHubModelsClient(
        api_key="github-pat",
        base_url="https://models.github.ai/inference",
        api_version="2026-03-10",
    )
    fake_http = _FakeAsyncClient()
    client._client = fake_http

    result = asyncio.run(
        client(
            prompt="Return JSON only",
            model="openai/gpt-5-nano",
            temperature=0.1,
            max_tokens=256,
        )
    )

    assert result == '{"status":"ok"}'
    assert fake_http.calls == [
        (
            "https://models.github.ai/inference/chat/completions",
            {
                "model": "openai/gpt-5-nano",
                "messages": [{"role": "user", "content": "Return JSON only"}],
                "temperature": 0.1,
                "max_tokens": 256,
            },
        )
    ]
