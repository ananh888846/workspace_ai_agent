from __future__ import annotations

from typing import Any, Sequence

from app.application.knowledge.retrieval import KnowledgeResult, RetrievalCandidate


class PostgresKnowledgeAuthorizationRepository:
    """Canonical SQL authorization/provenance boundary for Knowledge retrieval."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def authorize_query(self, *, user_id: str, organization_id: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT 1
                FROM organization_members om
                JOIN user_roles ur ON ur.user_id = om.user_id
                JOIN role_permissions rp ON rp.role_id = ur.role_id
                JOIN permissions p ON p.id = rp.permission_id
                WHERE om.organization_id = %s
                  AND om.user_id = %s
                  AND om.status = 'active'
                  AND p.resource = 'knowledge'
                  AND p.action = 'read'
            )
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, [organization_id, user_id])
            row = cursor.fetchone()
        return bool(row and row[0])

    def filter_candidates(
        self,
        *,
        user_id: str,
        organization_id: str,
        candidates: Sequence[RetrievalCandidate],
    ) -> list[KnowledgeResult]:
        if not candidates:
            return []
        point_ids = [candidate.point_id for candidate in candidates]
        query = """
            SELECT
                kc.qdrant_point_id,
                ks.id,
                ks.provider,
                ks.external_id,
                ks.source_url,
                ks.canonical_url,
                kdv.id
            FROM knowledge_chunks kc
            JOIN knowledge_document_versions kdv
              ON kdv.id = kc.document_version_id
             AND kdv.organization_id = kc.organization_id
            JOIN knowledge_document_version_sources kdvs
              ON kdvs.document_version_id = kdv.id
             AND kdvs.organization_id = kdv.organization_id
            JOIN knowledge_sources ks
              ON ks.id = kdvs.source_id
             AND ks.organization_id = kdvs.organization_id
            LEFT JOIN user_accounts ua
              ON ua.id = ks.user_account_id
            LEFT JOIN account_grants ag
              ON ag.user_account_id = ks.user_account_id
             AND ag.organization_id = ks.organization_id
             AND ag.grantee_user_id = %s
             AND ag.status = 'active'
             AND ag.revoked_at IS NULL
             AND (ag.starts_at IS NULL OR ag.starts_at <= CURRENT_TIMESTAMP)
             AND (ag.expires_at IS NULL OR ag.expires_at > CURRENT_TIMESTAMP)
            WHERE kc.organization_id = %s
              AND kc.qdrant_point_id = ANY(%s)
              AND (
                    ks.user_account_id IS NULL
                    OR ua.user_id = %s
                    OR ag.id IS NOT NULL
              )
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                query,
                [user_id, organization_id, point_ids, user_id],
            )
            rows = cursor.fetchall()

        by_point = {
            str(row[0]): (
                str(row[1]),
                str(row[2]),
                str(row[3]),
                row[4],
                row[5],
                str(row[6]),
            )
            for row in rows
        }
        result: list[KnowledgeResult] = []
        for candidate in candidates:
            metadata = by_point.get(candidate.point_id)
            if metadata is None:
                continue
            source_id, provider, external_id, source_url, canonical_url, version_id = metadata
            result.append(
                KnowledgeResult(
                    point_id=candidate.point_id,
                    score=candidate.score,
                    content=candidate.content,
                    document_version_id=version_id,
                    chunk_index=candidate.chunk_index,
                    provider=provider,
                    source_url=source_url,
                    canonical_url=canonical_url,
                    external_id=external_id,
                    source_id=source_id,
                )
            )
        return result
