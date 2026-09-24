from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.llm.providers import LLMProvider, LLMProviderError


LLMMode = Literal["local", "cloud", "hybrid"]


class LLMResolutionError(RuntimeError):
    """Raised when the configured LLM mode cannot produce a provider."""


@dataclass(frozen=True)
class LLMResolver:
    """Resolve the provider according to the simple Multi-Hybrid LLM V1 policy.

    V1 policy:
    - local  -> local provider only
    - cloud  -> cloud provider only
    - hybrid -> local first, cloud fallback

    The resolver does not inspect identity, authorization, credentials, or
    capability policy.
    """

    local: LLMProvider
    cloud: LLMProvider | None = None
    mode: LLMMode = "local"

    def __post_init__(self) -> None:
        if self.mode not in {"local", "cloud", "hybrid"}:
            raise ValueError("unsupported_llm_mode")

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> tuple[str, str]:
        if self.mode == "local":
            return self._call(self.local, prompt, system_prompt=system_prompt, model=model)

        if self.cloud is None:
            raise LLMResolutionError("cloud_llm_not_configured")

        if self.mode == "cloud":
            return self._call(self.cloud, prompt, system_prompt=system_prompt, model=model)

        try:
            return self._call(self.local, prompt, system_prompt=system_prompt, model=model)
        except LLMProviderError as local_error:
            try:
                return self._call(self.cloud, prompt, system_prompt=system_prompt, model=model)
            except LLMProviderError as cloud_error:
                raise LLMResolutionError("local_and_cloud_llm_failed") from cloud_error
            except Exception as cloud_error:
                raise LLMResolutionError("cloud_llm_failed") from cloud_error
        except Exception as local_error:
            try:
                return self._call(self.cloud, prompt, system_prompt=system_prompt, model=model)
            except Exception as cloud_error:
                raise LLMResolutionError("local_and_cloud_llm_failed") from cloud_error

    @staticmethod
    def _call(
        provider: LLMProvider,
        prompt: str,
        *,
        system_prompt: str | None,
        model: str | None,
    ) -> tuple[str, str]:
        text = provider.generate(
            prompt,
            system_prompt=system_prompt,
            model=model,
        )
        return text, provider.name
