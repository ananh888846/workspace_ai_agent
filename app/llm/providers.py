from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLMProviderError(RuntimeError):
    """Base error for an LLM provider failure."""


class LLMProviderUnavailableError(LLMProviderError):
    """Provider is configured but cannot serve the request."""


class LLMProvider(Protocol):
    """Minimal provider contract used by the application LLM boundary."""

    name: str

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        """Generate text without receiving authz, credential, or provider state."""


@dataclass(frozen=True)
class LLMRequest:
    """Provider-neutral LLM request.

    This object intentionally contains prompt data only. It must never carry
    access tokens, refresh tokens, client secrets, credential objects, or
    authorization decisions.
    """

    prompt: str
    system_prompt: str | None = None
    model: str | None = None


@dataclass(frozen=True)
class LLMResponse:
    """Provider-neutral LLM response."""

    text: str
    provider: str
    model: str | None = None
