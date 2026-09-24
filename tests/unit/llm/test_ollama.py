from __future__ import annotations

import json

import pytest

from app.llm.providers import LLMProviderError, LLMProviderUnavailableError
from app.llm.ollama import OllamaProvider


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_ollama_provider_posts_generate_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse({"response": "xin chào"})

    monkeypatch.setattr("app.llm.ollama.urlopen", fake_urlopen)

    provider = OllamaProvider("http://localhost:11434", "qwen2.5:1.5b")
    assert provider.generate("hello", system_prompt="be concise") == "xin chào"
    assert captured["url"] == "http://localhost:11434/api/generate"
    assert captured["payload"] == {
        "model": "qwen2.5:1.5b",
        "prompt": "hello",
        "stream": False,
        "system": "be concise",
    }


def test_ollama_provider_maps_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from urllib.error import HTTPError

    def fake_urlopen(request, timeout):
        raise HTTPError(request.full_url, 503, "down", {}, None)

    monkeypatch.setattr("app.llm.ollama.urlopen", fake_urlopen)

    with pytest.raises(LLMProviderError, match="ollama_http_503"):
        OllamaProvider("http://localhost:11434", "qwen2.5:1.5b").generate("hello")


def test_ollama_provider_maps_connection_error(monkeypatch: pytest.MonkeyPatch) -> None:
    from urllib.error import URLError

    def fake_urlopen(request, timeout):
        raise URLError("connection refused")

    monkeypatch.setattr("app.llm.ollama.urlopen", fake_urlopen)

    with pytest.raises(LLMProviderUnavailableError, match="ollama_unavailable"):
        OllamaProvider("http://localhost:11434", "qwen2.5:1.5b").generate("hello")


def test_ollama_provider_maps_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    class InvalidResponse(FakeResponse):
        def read(self):
            return b"not-json"

    def fake_urlopen(request, timeout):
        return InvalidResponse({})

    monkeypatch.setattr("app.llm.ollama.urlopen", fake_urlopen)

    with pytest.raises(LLMProviderError, match="ollama_invalid_response"):
        OllamaProvider("http://localhost:11434", "qwen2.5:1.5b").generate("hello")


def test_ollama_provider_maps_missing_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout):
        return FakeResponse({"done": True})

    monkeypatch.setattr("app.llm.ollama.urlopen", fake_urlopen)

    with pytest.raises(LLMProviderError, match="ollama_response_missing"):
        OllamaProvider("http://localhost:11434", "qwen2.5:1.5b").generate("hello")
