from app.application.knowledge.retrieval import (
    KnowledgeRetrievalService,
    RerankedKnowledgeRetrievalService,
    RetrievalCandidate,
)


class Embedding:
    def embed(self, chunks):
        return [[0.1, 0.2]]


class Vector:
    def search(self, vector, *, organization_id, limit):
        return [
            RetrievalCandidate("p1", 0.7, "alpha", "v1", 0),
            RetrievalCandidate("p2", 0.6, "beta", "v1", 1),
        ][:limit]


class Reranker:
    def rerank(self, query, candidates):
        return list(reversed(candidates))


def test_k7_query_embedding_and_tenant_retrieval():
    result = KnowledgeRetrievalService(Embedding(), Vector()).retrieve(
        "hello", organization_id="org-1", limit=2
    )
    assert [item.point_id for item in result] == ["p1", "p2"]


def test_k8_reranking_reorders_candidates():
    result = RerankedKnowledgeRetrievalService(
        KnowledgeRetrievalService(Embedding(), Vector()), Reranker()
    ).retrieve("hello", organization_id="org-1", candidate_limit=2, limit=2)
    assert [item.point_id for item in result] == ["p2", "p1"]
