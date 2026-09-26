from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace

from app.application.capabilities.knowledge import KnowledgeHandler


class _Authorization:
    def __init__(self, allowed: bool):
        self.allowed = allowed

    def authorize_query(self, **_: object) -> bool:
        return self.allowed

    def filter_candidates(self, *, candidates, **_):
        return [
            SimpleNamespace(
                point_id=c.point_id,
                score=c.score,
                content=c.content,
                document_version_id=c.document_version_id,
                chunk_index=c.chunk_index,
                provider="test",
                source_url=None,
                canonical_url=None,
                external_id="e2e",
                source_id="source",
            )
            for c in candidates
        ]


class _Embedding:
    def embed(self, chunks):
        return [[0.1, 0.2]]


class _VectorIndex:
    def search(self, vector, *, organization_id, limit):
        return [
            SimpleNamespace(
                point_id="point-1",
                score=0.5,
                content="PostgreSQL canonical document",
                document_version_id="version-1",
                chunk_index=0,
            )
        ]


class _Reranker:
    def __init__(self, model_name):
        self.model_name = model_name

    def rerank(self, query, candidates):
        return list(candidates)


class _Connection:
    pass


def _request():
    return SimpleNamespace(
        message="Where is the document stored?",
        conversation_id="conversation-1",
        max_results=2,
    )


def test_knowledge_handler_denies_before_provider_construction(monkeypatch):
    created = {"embedding": 0, "qdrant": 0, "reranker": 0}

    @contextmanager
    def fake_connection():
        yield _Connection()

    class DeniedAuthorization(_Authorization):
        def __init__(self, connection):
            super().__init__(False)

    class ForbiddenEmbedding:
        def __init__(self, *args, **kwargs):
            created["embedding"] += 1

    class ForbiddenQdrant:
        def __init__(self, *args, **kwargs):
            created["qdrant"] += 1

    class ForbiddenReranker:
        def __init__(self, *args, **kwargs):
            created["reranker"] += 1

    monkeypatch.setattr(
        "app.application.capabilities.knowledge.database_connection",
        fake_connection,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.PostgresKnowledgeAuthorizationRepository",
        DeniedAuthorization,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.OllamaEmbeddingProvider",
        ForbiddenEmbedding,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.QdrantVectorIndex",
        ForbiddenQdrant,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.BGEReranker",
        ForbiddenReranker,
    )

    state = {
        "request": _request(),
        "context": {
            "user_id": "user-1",
            "organization_id": "org-1",
        },
    }

    result = KnowledgeHandler().handle(state)

    assert result["status"] == "authorization_denied"
    assert result["provider_called"] is False
    assert created == {"embedding": 0, "qdrant": 0, "reranker": 0}


def test_knowledge_handler_uses_configured_bge_reranker(monkeypatch):
    captured = {}

    @contextmanager
    def fake_connection():
        yield _Connection()

    class AllowedAuthorization(_Authorization):
        def __init__(self, connection):
            super().__init__(True)

    class FakeReranker(_Reranker):
        def __init__(self, model_name):
            captured["model_name"] = model_name
            super().__init__(model_name)

    class FakeSettings:
        ollama_base_url = "http://ollama"
        ollama_embedding_model = "embedding-model"
        qdrant_url = "http://qdrant"
        qdrant_collection = "knowledge_v1"
        knowledge_reranker_enabled = True
        knowledge_reranker_model = "BAAI/bge-reranker-v2-m3"

    monkeypatch.setattr(
        "app.application.capabilities.knowledge.database_connection",
        fake_connection,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.PostgresKnowledgeAuthorizationRepository",
        AllowedAuthorization,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.OllamaEmbeddingProvider",
        lambda *args, **kwargs: _Embedding(),
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.QdrantVectorIndex",
        lambda *args, **kwargs: _VectorIndex(),
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.BGEReranker",
        FakeReranker,
    )
    monkeypatch.setattr(
        "app.application.capabilities.knowledge.get_settings",
        lambda: FakeSettings(),
    )

    state = {
        "request": _request(),
        "context": {
            "user_id": "user-1",
            "organization_id": "org-1",
        },
    }

    result = KnowledgeHandler().handle(state)

    assert result["status"] == "ok"
    assert result["provider_called"] is True
    assert captured["model_name"] == "BAAI/bge-reranker-v2-m3"
    assert result["data"]["results"][0]["content"] == "PostgreSQL canonical document"
