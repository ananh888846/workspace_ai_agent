#!/usr/bin/env python3
"""Local Knowledge retrieval quality benchmark.

This benchmark intentionally uses hard negatives: multiple documents discuss
closely related concepts, while each query is paraphrased so it does not simply
repeat the target document's keywords.

It compares first-stage cosine retrieval from Ollama embeddings with BGE
cross-encoder reranking using the same 30-candidate ceiling as the production
Knowledge retrieval path. It does not modify PostgreSQL or Qdrant data.

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
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.application.knowledge.retrieval import RetrievalCandidate
from app.infrastructure.knowledge.bge_reranker import BGEReranker
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider


@dataclass(frozen=True)
class BenchmarkCase:
    query: str
    relevant_id: str


# The queries deliberately use paraphrases and avoid simply copying the
# terminology from the relevant fixture. Each topic also has several
# semantically similar hard negatives.
CASES = (
    BenchmarkCase(
        "Thành phần nào giữ chỉ mục vector để tìm các đoạn nội dung theo ngữ nghĩa?",
        "qdrant_primary",
    ),
    BenchmarkCase(
        "Dịch vụ nào biến văn bản thành biểu diễn số để phục vụ tìm kiếm?",
        "ollama_primary",
    ),
    BenchmarkCase(
        "Công cụ nào xếp hạng lại các ứng viên sau lần tìm kiếm đầu tiên?",
        "bge_primary",
    ),
    BenchmarkCase(
        "Kho dữ liệu nào là nơi lưu bản ghi Knowledge chuẩn làm nguồn sự thật?",
        "postgres_primary",
    ),
    BenchmarkCase(
        "Trước khi trả nội dung nội bộ, hệ thống dựa vào cơ chế nào để quyết định người dùng được phép đọc?",
        "authorization_primary",
    ),
    BenchmarkCase(
        "Khi một tài liệu mới thay thế bản cũ, hệ thống phải làm gì với dữ liệu lập chỉ mục cũ?",
        "lifecycle_primary",
    ),
    BenchmarkCase(
        "Tìm kiếm theo nghĩa dùng kho nào làm lớp chỉ mục dẫn xuất thay vì nguồn dữ liệu gốc?",
        "qdrant_primary",
    ),
    BenchmarkCase(
        "Mô hình embedding được gọi ở bước nào trước khi nội dung đi vào vector store?",
        "ollama_primary",
    ),
    BenchmarkCase(
        "Sau khi lọc quyền và lấy các ứng viên, thành phần nào quyết định thứ tự cuối cùng?",
        "bge_primary",
    ),
    BenchmarkCase(
        "Thông tin phiên bản, chunk và provenance của Knowledge được lưu bền vững ở đâu?",
        "postgres_primary",
    ),
    BenchmarkCase(
        "Lớp nào ngăn người dùng nhận tài liệu của organization khác?",
        "authorization_primary",
    ),
    BenchmarkCase(
        "Khi số chunk của một phiên bản thay đổi, bước nào dọn các vector không còn tương ứng?",
        "lifecycle_primary",
    ),
)


# Six related documents per topic create realistic hard negatives. The primary
# document is the only relevant document for each case; related documents are
# intentionally plausible but answer a different question.
DOCUMENTS = (
    ("qdrant_primary", "Qdrant is the derived vector index used for tenant-filtered semantic retrieval of Knowledge chunks."),
    ("qdrant_similarity", "Vector search compares embedding similarity and returns candidate Knowledge chunks for a later ranking stage."),
    ("qdrant_payload", "Knowledge vector records carry organization, document version, chunk index, and content payload metadata."),
    ("qdrant_reconcile", "Vector reconciliation removes stale points when a Knowledge document version no longer contains those chunks."),
    ("qdrant_storage", "Qdrant stores derived vector representations while PostgreSQL remains the canonical Knowledge store."),
    ("qdrant_filter", "Semantic retrieval applies an exact organization filter so vector candidates remain inside the current tenant."),
    ("ollama_primary", "Ollama creates embeddings for Knowledge chunks and user queries before semantic vector retrieval."),
    ("ollama_model", "The local embedding model converts text into fixed-size numerical vectors for similarity comparison."),
    ("ollama_runtime", "The embedding provider calls the local Ollama service and returns vectors to the Knowledge ingestion pipeline."),
    ("ollama_query", "User questions are embedded into the same vector space used by indexed Knowledge chunks."),
    ("ollama_retry", "Embedding generation can be retried after a temporary model or local service failure during ingestion."),
    ("ollama_generation", "Ollama can run local language models, while the Knowledge pipeline specifically uses its embedding capability for vectors."),
    ("bge_primary", "BGE reranks authorized semantic-retrieval candidates as a second-stage cross-encoder ranking model."),
    ("bge_candidates", "The reranker receives a query and candidate passages after the first vector-search stage."),
    ("bge_authorized", "Only candidates that already passed Knowledge authorization should be sent into the reranking stage."),
    ("bge_model", "BAAI/bge-reranker-v2-m3 scores query-document pairs to refine the order of retrieved passages."),
    ("bge_latency", "Cross-encoder reranking adds a second computation after vector retrieval and therefore has a separate runtime cost."),
    ("bge_evaluation", "A reranker should be evaluated with ranking metrics rather than assuming that model execution proves retrieval quality."),
    ("postgres_primary", "PostgreSQL stores canonical Knowledge sources, document versions, chunks, and provenance metadata."),
    ("postgres_version", "Knowledge document versions in PostgreSQL track status, version number, and content checksum."),
    ("postgres_chunks", "Canonical Knowledge chunks are persisted in PostgreSQL so the source content remains recoverable independently of the vector index."),
    ("postgres_provenance", "Knowledge provenance records describe where canonical content came from and how it relates to source documents."),
    ("postgres_transaction", "Ingestion persists canonical database state before the derived vector index is reconciled."),
    ("postgres_source", "Knowledge source records identify the origin of canonical documents and their active versions."),
    ("authorization_primary", "PostgreSQL checks Knowledge read permission and source or account access before results are returned."),
    ("authorization_tenant", "Organization filtering prevents a Knowledge query from returning vectors belonging to another tenant."),
    ("authorization_role", "Permission catalog entries define whether an authenticated role can perform the Knowledge read capability."),
    ("authorization_provider", "Knowledge providers should not be constructed or called when authorization denies the requested operation."),
    ("authorization_scope", "A valid authentication identity does not by itself grant access to every Knowledge source."),
    ("authorization_audit", "Authorization decisions are part of the protected Knowledge retrieval boundary before provider results are exposed."),
    ("lifecycle_primary", "When a Knowledge version is replaced, the old version is superseded and its derived Qdrant vectors are removed."),
    ("lifecycle_delete", "Deleting a Knowledge source retires its active versions and removes their derived vector points."),
    ("lifecycle_reingest", "A deleted Knowledge version with the same checksum can be reactivated instead of creating a duplicate canonical version."),
    ("lifecycle_reconcile", "Vector reconciliation removes stale chunk points so the derived index exactly matches the active chunk set."),
    ("lifecycle_idempotent", "Re-ingesting unchanged healthy content should avoid creating duplicate versions or unnecessary embeddings."),
    ("lifecycle_canonical", "PostgreSQL remains canonical while Qdrant is treated as rebuildable derived retrieval state."),
)

# Production retrieval keeps at least 30 candidates when reranking is enabled.
# Limiting the benchmark to the same candidate ceiling makes the comparison
# representative without requiring a live Qdrant collection.
RERANK_CANDIDATE_LIMIT = 30


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


def rank_of(ids: list[str], relevant_id: str) -> int | None:
    try:
        return ids.index(relevant_id) + 1
    except ValueError:
        return None


def reciprocal_rank(ids: list[str], relevant_id: str, k: int) -> float:
    rank = rank_of(ids[:k], relevant_id)
    return 0.0 if rank is None else 1.0 / rank


def recall_at_k(ids: list[str], relevant_id: str, k: int) -> float:
    return float(relevant_id in ids[:k])


def precision_at_k(ids: list[str], relevant_id: str, k: int) -> float:
    return float(relevant_id in ids[:k]) / k


def ndcg_at_k(ids: list[str], relevant_id: str, k: int) -> float:
    rank = rank_of(ids[:k], relevant_id)
    return 0.0 if rank is None else 1.0 / math.log2(rank + 1)


def mean_metric(
    cases: tuple[BenchmarkCase, ...],
    ranked_cases: list[list[RetrievalCandidate]],
    metric,
    k: int,
) -> float:
    return sum(
        metric(
            [candidate.point_id for candidate in candidates],
            case.relevant_id,
            k,
        )
        for case, candidates in zip(cases, ranked_cases)
    ) / len(cases)


def build_baseline(
    query_vectors: list[list[float]],
    document_ids: list[str],
    document_texts: list[str],
    document_vectors: list[list[float]],
) -> list[list[RetrievalCandidate]]:
    ranked_cases = []
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
        ranked_cases.append(scored)
    return ranked_cases


def print_metrics(
    cases: tuple[BenchmarkCase, ...],
    baseline_cases: list[list[RetrievalCandidate]],
    reranked_cases: list[list[RetrievalCandidate]],
) -> None:
    for k in (1, 3, 5, 10):
        baseline_recall = mean_metric(cases, baseline_cases, recall_at_k, k)
        reranked_recall = mean_metric(cases, reranked_cases, recall_at_k, k)
        baseline_precision = mean_metric(cases, baseline_cases, precision_at_k, k)
        reranked_precision = mean_metric(cases, reranked_cases, precision_at_k, k)
        baseline_ndcg = mean_metric(cases, baseline_cases, ndcg_at_k, k)
        reranked_ndcg = mean_metric(cases, reranked_cases, ndcg_at_k, k)
        print(
            f"@{k}: "
            f"Recall baseline={baseline_recall:.3f} reranked={reranked_recall:.3f} | "
            f"Precision baseline={baseline_precision:.3f} reranked={reranked_precision:.3f} | "
            f"nDCG baseline={baseline_ndcg:.3f} reranked={reranked_ndcg:.3f}"
        )

    baseline_mrr = mean_metric(cases, baseline_cases, reciprocal_rank, 10)
    reranked_mrr = mean_metric(cases, reranked_cases, reciprocal_rank, 10)
    print(f"MRR@10: baseline={baseline_mrr:.3f} reranked={reranked_mrr:.3f}")


def main() -> int:
    base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    model = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe:latest")
    embedding = OllamaEmbeddingProvider(base_url=base_url, model=model)

    document_ids = [item[0] for item in DOCUMENTS]
    document_texts = [item[1] for item in DOCUMENTS]
    document_vectors = embedding.embed(document_texts)
    query_vectors = embedding.embed([case.query for case in CASES])

    baseline_cases = build_baseline(
        query_vectors,
        document_ids,
        document_texts,
        document_vectors,
    )

    reranker = BGEReranker(
        model_name=os.getenv(
            "KNOWLEDGE_RERANKER_MODEL",
            "BAAI/bge-reranker-v2-m3",
        )
    )
    reranked_cases = [
        reranker.rerank(case.query, candidates[:RERANK_CANDIDATE_LIMIT])
        for case, candidates in zip(CASES, baseline_cases)
    ]

    print("Knowledge Retrieval Quality Benchmark")
    print(f"Cases: {len(CASES)}")
    print(f"Fixture documents: {len(DOCUMENTS)}")
    print(f"BGE candidate limit: {RERANK_CANDIDATE_LIMIT}")
    print("Corpus design: paraphrased queries + hard negatives")
    print(f"Ollama embedding model: {model}")
    print(f"BGE model: {reranker.model_name}")
    print()
    print_metrics(CASES, baseline_cases, reranked_cases)
    print()

    for case, baseline, reranked in zip(CASES, baseline_cases, reranked_cases):
        baseline_ids = [candidate.point_id for candidate in baseline]
        reranked_ids = [candidate.point_id for candidate in reranked]
        print(f"Query: {case.query}")
        print(f"  expected: {case.relevant_id}")
        print(
            f"  rank: baseline={rank_of(baseline_ids, case.relevant_id) or 'not found'} "
            f"reranked={rank_of(reranked_ids, case.relevant_id) or 'not found'}"
        )
        print("  baseline:", ", ".join(baseline[:10][i].point_id for i in range(min(10, len(baseline)))))
        print("  reranked:", ", ".join(reranked[:10][i].point_id for i in range(min(10, len(reranked)))))
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
