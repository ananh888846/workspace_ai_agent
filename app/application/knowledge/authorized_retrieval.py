"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Enforces query authorization and canonical source-level filtering around Knowledge retrieval.\n"""\n\nfrom __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from app.application.knowledge.retrieval import KnowledgeResult, RetrievalCandidate


class KnowledgeQueryAuthorizationPort(Protocol):
    def authorize_query(self, *, user_id: str, organization_id: str) -> bool: ...

    def filter_candidates(
        self,
        *,
        user_id: str,
        organization_id: str,
        candidates: Sequence[RetrievalCandidate],
    ) -> list[KnowledgeResult]: ...


@dataclass
class AuthorizedKnowledgeRetrievalService:
    """K9 authorization + canonical provenance reconstruction.

    Authorization is checked before retrieval. Candidate chunks are already
    tenant-filtered in Qdrant; PostgreSQL then reconstructs canonical source
    metadata and applies source/account access rules.
    """

    retrieval: object
    authorization: KnowledgeQueryAuthorizationPort

    def retrieve(
        self,
        query: str,
        *,
        user_id: str,
        organization_id: str,
        limit: int = 10,
    ) -> list[KnowledgeResult]:
        if not self.authorization.authorize_query(
            user_id=user_id,
            organization_id=organization_id,
        ):
            return []
        candidates = self.retrieval.retrieve(
            query,
            organization_id=organization_id,
            limit=max(limit, 1),
        )
        authorized = self.authorization.filter_candidates(
            user_id=user_id,
            organization_id=organization_id,
            candidates=candidates,
        )
        return authorized[:limit]
