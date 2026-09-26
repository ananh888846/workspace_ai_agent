#!/usr/bin/env python3
"""Local Knowledge retrieval quality benchmark.

Compares first-stage cosine retrieval from Ollama embeddings with BGE
cross-encoder reranking. It intentionally uses a small deterministic fixture
so the benchmark can run without modifying PostgreSQL or Qdrant data.

Run from the repository root:
    python scripts/knowledge_retrieval_benchmark.py

Required local services/packages:
    OLLAMA_BASE_URL (default http://127.0.0.1:11434)
    OLLAMA_EMBEDDING_MODEL (default nomic-embed-text-v2-moe:latest)
    sentence-transformers
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass

from app.application.knowledge.retrieval import RetrievalCandidate
from app.infrastructure.knowledge.bge_reranker import BGEReranker
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    relevant_id: str


CASES = (
    BenchmarkCase(
        "Qdrant dùng để làm gì trong hệ thống?",
        "qdrant",
    ),
    BenchmarkCase(
        "Thành phần nào tạo vector embedding?",
        "ollama",
    ),
    BenchmarkCase(
        "BGE được dùng ở bước nào?",
        "bge",
    ),
    BenchmarkCase(
        "Dữ liệu Knowledge canonical được lưu ở đâu?",
        "postgres",
    ),
    BenchmarkCase(
        "Hệ thống kiểm tra quyền truy cập Knowledge như thế nào?",
        "authorization",
    ),
)

DOCUMENTS = (
    (
        "postgres",
        "PostgreSQL stores canonical Knowledge sources, document versions, chunks, and provenance metadata.",
    ),
    (
        "qdrant",
        "Qdrant is the derived vector index used for tenant-filtered semantic retrieval.",
    ),
    (
        "ollama",
        "Ollama creates embeddings for Knowledge chunks and user queries.",
    ),
    (
        "bge",
        "BGE reranks the authorized semantic-retrieval candidates as a second-stage ranking model.",
    ),
    (
        "authorization",
        "PostgreSQL checks Knowledge read permission and source/account access before results are returned.",
    ),
    (
        "calendar",
        "Google Calendar integration reads and writes calendar events and free-busy information.",
    ),
)


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def reciprocal_rank(ids: list[str], relevant_id: str, k: int) -> float:
    try:
        rank = ids[:k].index(relevant_id) + 1
    except ValueError:
        return 0.0
    return 1.0 / rank


def recall_at_k(ids: list[str], relevant_id: str, k: int) -> float:
    return float(relevant_id in ids[:k])


def main() -> int:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe:latest")
    embedding = OllamaEmbeddingProvider(base_url=base_url, model=model)

    document_ids = [item[0] for item in DOCUMENTS]
    document_texts = [item[1] for item in DOCUMENTS]
    document_vectors = embedding.embed(document_texts)
    query_vectors = embedding.embed([case.query for case in CASES])

    baseline_cases: list[list[RetrievalCandidate]] = []
    for query_vector in query_vectors:
        scored = sorted(
            (
                RetrievalCandidate(
                    point_id=document_id,
                    score=cosine(query_vector, document_vector),
                    content=document_text,
                    document_version_id=document_id,
                    chunk_index=0,
                )
                for document_id, document_text, document_vector in zip(
                    document_ids, document_texts, document_vectors
                )
            ),
            key=lambda candidate: candidate.score,
            reverse=True,
        )
        baseline_cases.append(scored)

    reranker = BGEReranker(
        model_name=os.getenv(
            "KNOWLEDGE_RERANKER_MODEL",
            "BAAI/bge-reranker-v2-m3",
        )
    )
    reranked_cases = [
        reranker.rerank(case.query, candidates)
        for case, candidates in zip(CASES, baseline_cases)
    ]

    print("Knowledge Retrieval Quality Benchmark")
    print(f"Ollama embedding model: {model}")
    print(f"BGE model: {reranker.model_name}")
    print()

    for k in (1, 3, 5):
        baseline_recall = sum(
            recall_at_k(
                [candidate.point_id for candidate in candidates],
                case.relevant_id,
                k,
            )
            for case, candidates in zip(CASES, baseline_cases)
        ) / len(CASES)
        reranked_recall = sum(
            recall_at_k(
                [candidate.point_id for candidate in candidates],
                case.relevant_id,
                k,
            )
            for case, candidates in zip(CASES, reranked_cases)
        ) / len(CASES)
        print(f"Recall@{k}: baseline={baseline_recall:.3f} reranked={reranked_recall:.3f}")

    baseline_mrr = sum(
        reciprocal_rank(
            [candidate.point_id for candidate in candidates],
            case.relevant_id,
            5,
        )
        for case, candidates in zip(CASES, baseline_cases)
    ) / len(CASES)
    reranked_mrr = sum(
        reciprocal_rank(
            [candidate.point_id for candidate in candidates],
            case.relevant_id,
            5,
        )
        for case, candidates in zip(CASES, reranked_cases)
    ) / len(CASES)

    print(f"MRR@5:    baseline={baseline_mrr:.3f} reranked={reranked_mrr:.3f}")
    print()
    for case, baseline, reranked in zip(CASES, baseline_cases, reranked_cases):
        print(f"Query: {case.query}")
        print(f"  expected: {case.relevant_id}")
        print("  baseline:", ", ".join(candidate.point_id for candidate in baseline[:5]))
        print("  reranked:", ", ".join(candidate.point_id for candidate in reranked[:5]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
