\n"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.\n"""\n\nfrom __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class RetrievalCandidate:
    point_id: str
    score: float
    content: str
    document_version_id: str
    chunk_index: int


@dataclass(frozen=True)
class KnowledgeResult:
    point_id: str
    score: float
    content: str
    document_version_id: str
    chunk_index: int
    provider: str | None = None
    source_url: str | None = None
    canonical_url: str | None = None
    external_id: str | None = None
    source_id: str | None = None


class QueryEmbeddingPort(Protocol):
    def embed(self, chunks: list[str]) -> list[list[float]]: ...


class VectorSearchPort(Protocol):
    def search(
        self,
        vector: list[float],
        *,
        organization_id: str,
        limit: int,
    ) -> list[RetrievalCandidate]: ...


class RerankerPort(Protocol):
    def rerank(self, query: str, candidates: Sequence[RetrievalCandidate]) -> list[RetrievalCandidate]: ...


class KnowledgeRetrievalService:
    """K7 baseline semantic retrieval: query embedding -> Qdrant candidates."""

    def __init__(self, embedding: QueryEmbeddingPort, vector_index: VectorSearchPort) -> None:
        self.embedding = embedding
        self.vector_index = vector_index

    def retrieve(
        self,
        query: str,
        *,
        organization_id: str,
        limit: int = 10,
    ) -> list[RetrievalCandidate]:
        if not query.strip():
            return []
        if limit < 1:
            raise ValueError("limit_must_be_positive")
        vectors = self.embedding.embed([query])
        if len(vectors) != 1:
            raise RuntimeError("query_embedding_shape_invalid")
        return self.vector_index.search(
            vectors[0],
            organization_id=organization_id,
            limit=limit,
        )


class RerankedKnowledgeRetrievalService:
    """K8 retrieval + second-stage reranking."""

    def __init__(self, retrieval: KnowledgeRetrievalService, reranker: RerankerPort) -> None:
        self.retrieval = retrieval
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
        *,
        organization_id: str,
        candidate_limit: int = 30,
        limit: int = 10,
    ) -> list[RetrievalCandidate]:
        candidates = self.retrieval.retrieve(
            query,
            organization_id=organization_id,
            limit=candidate_limit,
        )
        return self.reranker.rerank(query, candidates)[:limit]
