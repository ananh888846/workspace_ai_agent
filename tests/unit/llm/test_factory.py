from app.config.settings import Settings
from app.llm.factory import build_llm_resolver
from app.llm.ollama import OllamaProvider


def test_factory_builds_ollama_provider_in_local_mode() -> None:
    settings = Settings(
        llm_mode="local",
        ollama_base_url="http://localhost:11434",
        ollama_chat_model="qwen2.5:1.5b",
    )
    resolver = build_llm_resolver(settings)
    assert resolver.mode == "local"
    assert isinstance(resolver.local, OllamaProvider)
    assert resolver.local.base_url == "http://localhost:11434"
    assert resolver.local.default_model == "qwen2.5:1.5b"
