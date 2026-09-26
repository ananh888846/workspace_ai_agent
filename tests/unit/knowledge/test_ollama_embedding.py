"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Unit tests for Ollama embedding response parsing and validation.
"""\n\nfrom app.infrastructure.knowledge.ollama_embedding import (
    OllamaEmbeddingProvider,
)


def test_ollama_embedding_provider_parses_vectors(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"embeddings": [[0.1, 0.2], [0.3, 0.4]]}'

    monkeypatch.setattr(
        "app.infrastructure.knowledge.ollama_embedding.urlopen",
        lambda request, timeout: Response(),
    )

    vectors = OllamaEmbeddingProvider("http://ollama", "test-model").embed(
        ["one", "two"]
    )

    assert vectors == [[0.1, 0.2], [0.3, 0.4]]


def test_ollama_embedding_provider_rejects_shape(monkeypatch):
    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"embeddings": [[0.1]]}'

    monkeypatch.setattr(
        "app.infrastructure.knowledge.ollama_embedding.urlopen",
        lambda request, timeout: Response(),
    )

    try:
        OllamaEmbeddingProvider("http://ollama", "test-model").embed(
            ["one", "two"]
        )
    except RuntimeError as exc:
        assert "shape" in str(exc)
    else:
        raise AssertionError("expected embedding shape error")
