"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: PostgreSQL canonical Knowledge source, document version, chunk, and asset persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from psycopg.types.json import Json
from uuid import UUID, uuid5
import hashlib

from app.domain.knowledge.source import KnowledgeSourceItem


@dataclass(frozen=True)
class KnowledgeSourceRecord:
    id: str


@dataclass(frozen=True)
class KnowledgeDocumentVersionRecord:
    id: str


class PostgresKnowledgeRepository:
    """PostgreSQL source-of-truth adapter for Knowledge V1.

    This repository owns canonical source/document/version/provenance persistence.
    Chunk vectors remain behind VectorIndexPort.
    """

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def find_source(self, item: KnowledgeSourceItem) -> KnowledgeSourceRecord | None:
        query = """
            SELECT id
            FROM knowledge_sources
            WHERE organization_id = %s
              AND user_account_id IS NOT DISTINCT FROM %s
              AND provider = %s
              AND resource_type = %s
              AND external_id = %s
            LIMIT 1
        """
        with self._connection.cursor() as cursor:
            cursor.execute(
                query,
                [
                    item.organization_id,
                    item.user_account_id,
                    item.provider,
                    item.resource_type,
                    item.external_id,
                ],
            )
            row = cursor.fetchone()

        return KnowledgeSourceRecord(id=str(row[0])) if row else None

    def create_source(self, item: KnowledgeSourceItem) -> KnowledgeSourceRecord:
        existing = self.find_source(item)
        if existing is not None:
            return existing

        query = """
            INSERT INTO knowledge_sources (
                organization_id,
                user_account_id,
                provider,
                resource_type,
                external_id,
                source_url,
                canonical_url,
                source_revision,
                source_checksum,
                status,
                metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
            RETURNING id
        """
        params = [
            item.organization_id,
            item.user_account_id,
            item.provider,
            item.resource_type,
            item.external_id,
            item.source_url,
            item.canonical_url,
            item.source_revision,
            item.source_checksum,
            "deleted" if item.deleted else "active",
            Json(item.metadata),
        ]

        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()

        if row is not None:
            self._connection.commit()
            return KnowledgeSourceRecord(id=str(row[0]))

        self._connection.rollback()
        existing = self.find_source(item)
        if existing is None:
            raise RuntimeError("knowledge_source_create_failed")
        return existing

    def current_checksum(self, source_id: str) -> str | None:
        query = """
            SELECT checksum
            FROM knowledge_document_versions kdvv
            JOIN knowledge_document_version_sources kdvs
              ON kdvs.document_version_id = kdvv.id
            WHERE kdvs.source_id = %s
            ORDER BY kdvv.version_no DESC
            LIMIT 1
        """
        with self._connection.cursor() as cursor:
            cursor.execute(query, [source_id])
            row = cursor.fetchone()

        return str(row[0]) if row and row[0] is not None else None

    def create_document_version(
        self,
        source_id: str,
        item: KnowledgeSourceItem,
    ) -> KnowledgeDocumentVersionRecord:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT kd.id
                    FROM knowledge_documents kd
                    JOIN knowledge_document_version_sources kdvs
                      ON kdvs.organization_id = kd.organization_id
                    JOIN knowledge_document_versions kdv
                      ON kdv.id = kdvs.document_version_id
                     AND kdv.knowledge_document_id = kd.id
                     AND kdv.organization_id = kd.organization_id
                    WHERE kdvs.source_id = %s
                      AND kd.organization_id = %s
                    ORDER BY kdv.version_no DESC
                    LIMIT 1
                    """,
                    [source_id, item.organization_id],
                )
                document_row = cursor.fetchone()

                if document_row is None:
                    cursor.execute(
                        """
                        SELECT id
                        FROM knowledge_documents
                        WHERE organization_id = %s
                          AND source_type = %s
                          AND source_id = %s
                        ORDER BY created_at
                        LIMIT 1
                        """,
                        [item.organization_id, item.provider, item.external_id],
                    )
                    document_row = cursor.fetchone()

                if document_row is None:
                    cursor.execute(
                        """
                        INSERT INTO knowledge_documents (
                            organization_id,
                            resource_id,
                            title,
                            source_type,
                            source_id,
                            version,
                            checksum,
                            status
                        )
                        VALUES (%s, NULL, %s, %s, %s, %s, %s, 'active')
                        RETURNING id
                        """,
                        [
                            item.organization_id,
                            item.title,
                            item.provider,
                            item.external_id,
                            "1",
                            item.source_checksum,
                        ],
                    )
                    document_id = str(cursor.fetchone()[0])
                else:
                    document_id = str(document_row[0])

                cursor.execute(
                    """
                    SELECT COALESCE(MAX(version_no), 0) + 1
                    FROM knowledge_document_versions
                    WHERE knowledge_document_id = %s
                    """,
                    [document_id],
                )
                version_no = int(cursor.fetchone()[0])

                cursor.execute(
                    """
                    INSERT INTO knowledge_document_versions (
                        organization_id,
                        knowledge_document_id,
                        version_no,
                        source_revision,
                        checksum,
                        canonical_content,
                        content_type,
                        status,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'active', %s)
                    RETURNING id
                    """,
                    [
                        item.organization_id,
                        document_id,
                        version_no,
                        item.source_revision,
                        item.source_checksum,
                        item.content,
                        item.mime_type or "text/plain",
                        Json(item.metadata),
                    ],
                )
                version_id = str(cursor.fetchone()[0])

                cursor.execute(
                    """
                    INSERT INTO knowledge_document_version_sources (
                        organization_id,
                        document_version_id,
                        source_id,
                        relation_type
                    )
                    VALUES (%s, %s, %s, 'primary')
                    ON CONFLICT (document_version_id, source_id) DO NOTHING
                    """,
                    [item.organization_id, version_id, source_id],
                )

                # Keep the legacy document snapshot fields synchronized for
                # older readers while the version table remains canonical.
                cursor.execute(
                    """
                    UPDATE knowledge_documents
                    SET title = %s,
                        version = %s,
                        checksum = %s,
                        status = 'active',
                        updated_at = now()
                    WHERE id = %s
                    """,
                    [item.title, str(version_no), item.source_checksum, document_id],
                )

            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise

        return KnowledgeDocumentVersionRecord(id=version_id)

    def create_chunks(
        self,
        document_version_id: str,
        organization_id: str,
        chunks: Sequence[str],
    ) -> list[str]:
        """Persist canonical version-scoped chunks and return stable point IDs.

        Qdrant remains a derived index. PostgreSQL owns chunk identity/content,
        allowing retrieval to reconstruct canonical content and provenance.
        """
        try:
            chunk_ids: list[str] = []
            with self._connection.cursor() as cursor:
                for index, content in enumerate(chunks):
                    point_id = str(uuid5(UUID(document_version_id), f"chunk:{index}"))
                    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
                    cursor.execute(
                        """
                        INSERT INTO knowledge_chunks (
                            document_id, chunk_index, content_hash, qdrant_point_id,
                            token_count, organization_id, document_version_id, content
                        )
                        SELECT kdv.knowledge_document_id, %s, %s, %s, NULL,
                               %s, kdv.id, %s
                        FROM knowledge_document_versions kdv
                        WHERE kdv.id = %s AND kdv.organization_id = %s
                        ON CONFLICT (document_version_id, chunk_index)
                        DO UPDATE SET content_hash = EXCLUDED.content_hash,
                                      qdrant_point_id = EXCLUDED.qdrant_point_id,
                                      content = EXCLUDED.content
                        RETURNING id
                        """,
                        [index, content_hash, point_id, organization_id, content,
                         document_version_id, organization_id],
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise RuntimeError("knowledge_chunk_version_not_found")
                    chunk_ids.append(str(row[0]))
            self._connection.commit()
            return chunk_ids
        except Exception:
            self._connection.rollback()
            raise

    def create_assets(
        self,
        document_version_id: str,
        organization_id: str,
        assets: Sequence[Any],
    ) -> list[str]:
        """Persist asset metadata; binary payloads stay in File Storage."""
        try:
            asset_ids: list[str] = []
            with self._connection.cursor() as cursor:
                for asset in assets:
                    cursor.execute(
                        """
                        INSERT INTO knowledge_assets (
                            organization_id, document_version_id, asset_type,
                            file_name, mime_type, file_size, checksum,
                            storage_backend, storage_key, metadata
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        [organization_id, document_version_id, asset.asset_type,
                         asset.file_name, asset.mime_type, asset.file_size,
                         asset.checksum, asset.storage_backend, asset.storage_key,
                         Json(asset.metadata)],
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise RuntimeError("knowledge_asset_create_failed")
                    asset_ids.append(str(row[0]))
            self._connection.commit()
            return asset_ids
        except Exception:
            self._connection.rollback()
            raise

    def mark_unchanged(self, source_id: str) -> None:
        # Source checksum is already represented by the latest immutable
        # version. No canonical mutation is required for an unchanged fetch.
        return None
