"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.\n"""\n\nfrom __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class EmbeddingProviderError(RuntimeError):
    """Raised when the embedding provider rejects or corrupts a request."""


class EmbeddingProviderUnavailableError(EmbeddingProviderError):
    """Raised when the embedding provider cannot be reached."""


@dataclass(frozen=True)
class OllamaEmbeddingProvider:
    """Ollama /api/embed adapter behind the Knowledge EmbeddingPort."""

    base_url: str
    model: str
    timeout_seconds: float = 120.0

    def embed(self, chunks: list[str]) -> list[list[float]]:
        if not chunks:
            return []

        payload = {"model": self.model, "input": chunks}
        request = Request(
            f"{self.base_url.rstrip('/')}/api/embed",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise EmbeddingProviderError(f"ollama_embedding_http_{exc.code}") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise EmbeddingProviderUnavailableError(
                "ollama_embedding_unavailable"
            ) from exc
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise EmbeddingProviderError(
                "ollama_embedding_invalid_response"
            ) from exc

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(chunks):
            raise EmbeddingProviderError("ollama_embedding_shape_invalid")

        result: list[list[float]] = []
        for vector in embeddings:
            if not isinstance(vector, list) or not vector:
                raise EmbeddingProviderError("ollama_embedding_vector_invalid")
            try:
                result.append([float(value) for value in vector])
            except (TypeError, ValueError) as exc:
                raise EmbeddingProviderError(
                    "ollama_embedding_vector_invalid"
                ) from exc
        return result
