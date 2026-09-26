"""
Created/Updated: 2026-09-26 GMT+7
Main Function: Real PostgreSQL + Qdrant Knowledge lifecycle E2E tests.
"""

from __future__ import annotations

import hashlib
import os
from uuid import uuid5, UUID

import pytest

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

from app.application.knowledge.ingest import KnowledgeIngestionService
from app.domain.knowledge.source import KnowledgeSourceItem
from app.infrastructure.database.repositories.knowledge import PostgresKnowledgeRepository
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex


pytestmark = pytest.mark.integration

ORG_ID = "8b7f6c5d-4e3f-4a2b-9c1d-7e6f5a4b3c21"
USER_ID = "8b7f6c5d-4e3f-4a2b-9c1d-7e6f5a4b3c22"
ROLE_ID = "8b7f6c5d-4e3f-4a2b-9c1d-7e6f5a4b3c23"
ROLE_NAME = "knowledge_lifecycle_e2e"


class AllowIngestion:
    def authorize_ingestion(self, **_: object) -> bool:
        return True


VECTOR_SIZE = 768


class DeterministicEmbedding:
    def embed(self, chunks):
        return [[0.1] * VECTOR_SIZE for _ in chunks]


class ParagraphChunker:
    def chunk(self, content: str) -> list[str]:
        return [part for part in content.split("\n\n") if part]


def _connection():
    if psycopg is None:
        pytest.skip("psycopg is not installed")
    return psycopg.connect(
        os.getenv(
            "DATABASE_URL",
            "postgresql://workspace:workspace_dev_password@127.0.0.1:5433/workspace_ai_agent",
        )
    )


def _create_test_organization(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO organizations (id, name, organization_type)
            VALUES (%s, 'Knowledge Qdrant Lifecycle E2E', 'workspace')
            ON CONFLICT (id) DO NOTHING
            """,
            [ORG_ID],
        )
    connection.commit()


def _cleanup(connection, qdrant, version_ids=()):
    connection.rollback()
    for version_id in version_ids:
        if version_id:
            qdrant.delete_document_version(version_id)
    qdrant._request(
        "POST",
        f"/collections/{qdrant.collection}/points/delete?wait=true",
        {
            "filter": {
                "must": [
                    {"key": "organization_id", "match": {"value": ORG_ID}}
                ]
            }
        },
    )
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM knowledge_document_version_sources WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute("DELETE FROM knowledge_assets WHERE organization_id = %s", [ORG_ID])
        cursor.execute("DELETE FROM knowledge_chunks WHERE organization_id = %s", [ORG_ID])
        cursor.execute(
            "DELETE FROM knowledge_document_versions WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute("DELETE FROM knowledge_sources WHERE organization_id = %s", [ORG_ID])
        cursor.execute("DELETE FROM knowledge_documents WHERE organization_id = %s", [ORG_ID])
        cursor.execute("DELETE FROM organizations WHERE id = %s", [ORG_ID])
    connection.commit()


def _scroll_version(qdrant, version_id):
    points = []
    offset = None
    while True:
        payload = {
            "limit": 1000,
            "with_payload": True,
            "with_vector": False,
            "filter": {
                "must": [
                    {"key": "document_version_id", "match": {"value": version_id}}
                ]
            },
        }
        if offset is not None:
            payload["offset"] = offset
        response = qdrant._request(
            "POST",
            f"/collections/{qdrant.collection}/points/scroll",
            payload,
        )
        result = response.get("result", {})
        points.extend(result.get("points", []))
        offset = result.get("next_page_offset")
        if offset is None:
            return points


def _item(content: str, checksum: str, deleted: bool = False):
    return KnowledgeSourceItem(
        organization_id=ORG_ID,
        user_account_id=None,
        provider="lifecycle_e2e",
        resource_type="document",
        external_id="lifecycle-001",
        content=content,
        source_checksum=checksum,
        title="Knowledge Lifecycle E2E",
        mime_type="text/plain",
        source_revision=checksum,
        deleted=deleted,
    )


@pytest.mark.skipif(
    os.getenv("RUN_KNOWLEDGE_LIFECYCLE_E2E") != "1",
    reason="set RUN_KNOWLEDGE_LIFECYCLE_E2E=1",
)
def test_real_postgres_qdrant_lifecycle():
    connection = _connection()
    qdrant = QdrantVectorIndex(
        os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
        os.getenv("QDRANT_COLLECTION", "knowledge_v1"),
    )
    version_ids = []
    try:
        _cleanup(connection, qdrant)
        _create_test_organization(connection)

        content_v1 = "canonical version one"
        content_v2 = "canonical version two\n\nsecond chunk"
        repository = PostgresKnowledgeRepository(connection)
        service = KnowledgeIngestionService(
            repository=repository,
            authorization=AllowIngestion(),
            chunker=ParagraphChunker(),
            embedding=DeterministicEmbedding(),
            vector_index=qdrant,
        )

        first = service.ingest(_item(content_v1, hashlib.sha256(content_v1.encode()).hexdigest()))
        assert first.status == "COMPLETED"
        version_ids.append(first.document_version_id)
        first_points = _scroll_version(qdrant, first.document_version_id)
        assert len(first_points) == 1

        second = service.ingest(_item(content_v2, hashlib.sha256(content_v2.encode()).hexdigest()))
        assert second.status == "COMPLETED"
        version_ids.append(second.document_version_id)
        second_points = _scroll_version(qdrant, second.document_version_id)
        assert len(second_points) == 2
        assert _scroll_version(qdrant, first.document_version_id) == []

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM knowledge_document_versions WHERE id = %s",
                [first.document_version_id],
            )
            assert cursor.fetchone()[0] == "superseded"
            cursor.execute(
                "SELECT status FROM knowledge_document_versions WHERE id = %s",
                [second.document_version_id],
            )
            assert cursor.fetchone()[0] == "active"

        point_ids_before = [str(point["id"]) for point in second_points]
        qdrant.upsert(
            [content_v2.split("\n\n")[0], content_v2.split("\n\n")[1]],
            [[0.1] * VECTOR_SIZE, [0.1] * VECTOR_SIZE],
            second.document_version_id,
            ORG_ID,
        )
        point_ids_after = [str(point["id"]) for point in _scroll_version(qdrant, second.document_version_id)]
        assert point_ids_after == point_ids_before

        stale_id = str(uuid5(UUID(second.document_version_id), "stale:999"))
        qdrant._request(
            "PUT",
            f"/collections/{qdrant.collection}/points?wait=true",
            {
                "points": [{
                    "id": stale_id,
                    "vector": [0.1] * VECTOR_SIZE,
                    "payload": {
                        "document_version_id": second.document_version_id,
                        "organization_id": ORG_ID,
                        "chunk_index": 999,
                        "content": "stale",
                    },
                }]
            },
        )
        assert any(str(point["id"]) == stale_id for point in _scroll_version(qdrant, second.document_version_id))
        qdrant.reconcile(second.document_version_id, [0, 1])
        assert all(str(point["id"]) != stale_id for point in _scroll_version(qdrant, second.document_version_id))

        deleted = service.ingest(
            _item(
                content_v2,
                hashlib.sha256(content_v2.encode()).hexdigest(),
                deleted=True,
            )
        )
        assert deleted.status == "DELETED"
        assert _scroll_version(qdrant, second.document_version_id) == []
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT status FROM knowledge_sources WHERE organization_id = %s",
                [ORG_ID],
            )
            assert cursor.fetchone()[0] == "deleted"
            cursor.execute(
                "SELECT status FROM knowledge_document_versions WHERE id = %s",
                [second.document_version_id],
            )
            assert cursor.fetchone()[0] == "deleted"
    finally:
        _cleanup(connection, qdrant, version_ids)
        connection.close()


@pytest.mark.skipif(
    os.getenv("RUN_KNOWLEDGE_LIFECYCLE_E2E") != "1",
    reason="set RUN_KNOWLEDGE_LIFECYCLE_E2E=1",
)
def test_real_qdrant_reconcile_paginates_over_1000_points():
    connection = _connection()
    qdrant = QdrantVectorIndex(
        os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
        os.getenv("QDRANT_COLLECTION", "knowledge_v1"),
    )
    version_ids = []
    try:
        _cleanup(connection, qdrant)
        _create_test_organization(connection)

        content = "\n\n".join(f"chunk-{index}" for index in range(1001))
        repository = PostgresKnowledgeRepository(connection)
        service = KnowledgeIngestionService(
            repository=repository,
            authorization=AllowIngestion(),
            chunker=ParagraphChunker(),
            embedding=DeterministicEmbedding(),
            vector_index=qdrant,
        )
        item = KnowledgeSourceItem(
            organization_id=ORG_ID,
            user_account_id=None,
            provider="lifecycle_pagination_e2e",
            resource_type="document",
            external_id="lifecycle-pagination-001",
            content=content,
            source_checksum=hashlib.sha256(content.encode()).hexdigest(),
            title="Knowledge Lifecycle Pagination E2E",
            mime_type="text/plain",
            source_revision="1001",
        )
        ingested = service.ingest(item)
        assert ingested.status == "COMPLETED"
        assert ingested.chunk_count == 1001
        version_ids.append(ingested.document_version_id)

        points = _scroll_version(qdrant, ingested.document_version_id)
        assert len(points) == 1001

        qdrant.reconcile(
            ingested.document_version_id,
            list(range(1000)),
        )

        remaining = _scroll_version(qdrant, ingested.document_version_id)
        assert len(remaining) == 1000
        assert all(
            int(point["payload"]["chunk_index"]) < 1000
            for point in remaining
        )
    finally:
        _cleanup(connection, qdrant, version_ids)
        connection.close()
