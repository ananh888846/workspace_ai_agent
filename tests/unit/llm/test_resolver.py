from __future__ import annotations

import pytest

from app.llm.providers import LLMProviderError
from app.llm.resolver import LLMResolutionError, LLMResolver


class FakeProvider:
    def __init__(self, name: str, response: str = "ok", error: Exception | None = None):
        self.name = name
        self.response = response
        self.error = error
        self.calls = 0

    def generate(self, prompt: str, *, system_prompt=None, model=None) -> str:
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


def test_local_mode_uses_only_local_provider() -> None:
    local = FakeProvider("ollama", "local")
    cloud = FakeProvider("cloud", "cloud")

    result = LLMResolver(local=local, cloud=cloud, mode="local").generate("hello")

    assert result == ("local", "ollama")
    assert local.calls == 1
    assert cloud.calls == 0


def test_cloud_mode_uses_only_cloud_provider() -> None:
    local = FakeProvider("ollama", "local")
    cloud = FakeProvider("cloud", "cloud")

    result = LLMResolver(local=local, cloud=cloud, mode="cloud").generate("hello")

    assert result == ("cloud", "cloud")
    assert local.calls == 0
    assert cloud.calls == 1


def test_hybrid_mode_uses_local_first_and_cloud_fallback() -> None:
    local = FakeProvider("ollama", error=LLMProviderError("local down"))
    cloud = FakeProvider("cloud", "cloud")

    result = LLMResolver(local=local, cloud=cloud, mode="hybrid").generate("hello")

    assert result == ("cloud", "cloud")
    assert local.calls == 1
    assert cloud.calls == 1


def test_hybrid_mode_does_not_call_cloud_after_local_success() -> None:
    local = FakeProvider("ollama", "local")
    cloud = FakeProvider("cloud", "cloud")

    result = LLMResolver(local=local, cloud=cloud, mode="hybrid").generate("hello")

    assert result == ("local", "ollama")
    assert local.calls == 1
    assert cloud.calls == 0


def test_cloud_and_hybrid_require_cloud_provider() -> None:
    local = FakeProvider("ollama", "local")

    with pytest.raises(LLMResolutionError, match="cloud_llm_not_configured"):
        LLMResolver(local=local, mode="cloud").generate("hello")

    with pytest.raises(LLMResolutionError, match="cloud_llm_not_configured"):
        LLMResolver(local=local, mode="hybrid").generate("hello")
