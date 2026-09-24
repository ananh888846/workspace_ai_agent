from __future__ import annotations

from app.config.settings import Settings, get_settings
from app.llm.ollama import OllamaProvider
from app.llm.resolver import LLMResolver


def build_llm_resolver(settings: Settings | None = None) -> LLMResolver:
    """Build the V1 resolver using the configured local Ollama provider.

    Cloud wiring is intentionally deferred to H3.
    """
    config = settings or get_settings()
    return LLMResolver(
        local=OllamaProvider(
            base_url=config.ollama_base_url,
            default_model=config.ollama_chat_model,
        ),
        mode=config.llm_mode,
    )
