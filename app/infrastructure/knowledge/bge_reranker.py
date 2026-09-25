"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Runs local BGE reranking over retrieved Knowledge candidates.
"""


from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.application.knowledge.retrieval import RetrievalCandidate


class RerankerError(RuntimeError):
    """Raised when the BGE reranker cannot execute."""


@dataclass
class BGEReranker:
    """Local BGE-Reranker-v2-m3 adapter behind RerankerPort.

    The model is loaded lazily so importing the Backend does not require
    heavyweight ML packages until reranking is actually requested.
    """

    model_name: str = "BAAI/bge-reranker-v2-m3"
    device: str | None = None

    def __post_init__(self) -> None:
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import CrossEncoder
        except ImportError as exc:
            raise RerankerError("sentence_transformers_not_installed") from exc
        try:
            self._model = CrossEncoder(self.model_name, device=self.device)
        except Exception as exc:
            raise RerankerError("bge_reranker_load_failed") from exc
        return self._model

    def rerank(
        self,
        query: str,
        candidates: Sequence[RetrievalCandidate],
    ) -> list[RetrievalCandidate]:
        if not candidates:
            return []
        model = self._load()
        try:
            scores = model.predict(
                [(query, candidate.content) for candidate in candidates]
            )
        except Exception as exc:
            raise RerankerError("bge_reranker_inference_failed") from exc
        ranked = sorted(
            zip(candidates, scores),
            key=lambda pair: float(pair[1]),
            reverse=True,
        )
        return [
            RetrievalCandidate(
                point_id=candidate.point_id,
                score=float(score),
                content=candidate.content,
                document_version_id=candidate.document_version_id,
                chunk_index=candidate.chunk_index,
            )
            for candidate, score in ranked
        ]
