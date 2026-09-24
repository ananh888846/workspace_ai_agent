from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.llm.providers import LLMProviderError, LLMProviderUnavailableError


@dataclass(frozen=True)
class OllamaProvider:
    """Adapter tối thiểu cho Ollama HTTP API.

    Chỉ nhận prompt/model; không nhận identity, authorization hoặc credential.
    """

    base_url: str
    default_model: str
    name: str = "ollama"
    timeout_seconds: float = 60.0

    def generate(
        self,
        prompt: str,
        *,
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> str:
        selected_model = model or self.default_model
        payload: dict[str, object] = {
            "model": selected_model,
            "prompt": prompt,
            "stream": False,
        }
        if system_prompt:
            payload["system"] = system_prompt

        request = Request(
            f"{self.base_url.rstrip('/')}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise LLMProviderError(f"ollama_http_{exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise LLMProviderUnavailableError("ollama_unavailable") from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise LLMProviderError("ollama_invalid_response") from exc

        text = data.get("response")
        if not isinstance(text, str):
            raise LLMProviderError("ollama_response_missing")
        return text
