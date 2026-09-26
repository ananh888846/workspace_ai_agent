"""
Created/Updated: 2026-09-26  GMT+7
Main Function: Full Knowledge E2E smoke test covering PostgreSQL canonical ingestion, Ollama embeddings, Qdrant retrieval, BGE reranking, authorization, and Vietnamese retrieval.
"""

from __future__ import annotations

import hashlib
import os
from uuid import UUID

import pytest

try:
    import psycopg
except ImportError:  # pragma: no cover
    psycopg = None

from app.application.knowledge.authorized_retrieval import (
    AuthorizedKnowledgeRetrievalService,
)
from app.application.knowledge.ingest import KnowledgeIngestionService
from app.application.knowledge.retrieval import (
    KnowledgeRetrievalService,
    RerankedKnowledgeRetrievalService,
)
from app.domain.knowledge.source import KnowledgeSourceItem
from app.infrastructure.database.repositories.knowledge import (
    PostgresKnowledgeRepository,
)
from app.infrastructure.database.repositories.knowledge_authorization import (
    PostgresKnowledgeAuthorizationRepository,
)
from app.infrastructure.knowledge.bge_reranker import BGEReranker
from app.infrastructure.knowledge.ollama_embedding import OllamaEmbeddingProvider
from app.infrastructure.knowledge.qdrant import QdrantVectorIndex


pytestmark = pytest.mark.integration

ORG_ID = "9b2e6b6a-4d8a-4b72-8c1e-9d8e5b8a7101"
USER_ID = "9b2e6b6a-4d8a-4b72-8c1e-9d8e5b8a7102"
ROLE_ID = "9b2e6b6a-4d8a-4b72-8c1e-9d8e5b8a7103"
VERSION_ID = "9b2e6b6a-4d8a-4b72-8c1e-9d8e5b8a7104"
ROLE_NAME = "knowledge_runtime_e2e"


class AllowIngestion:
    def authorize_ingestion(self, **_: object) -> bool:
        return True


class SimpleChunker:
    def chunk(self, content: str) -> list[str]:
        return [part.strip() for part in content.split("\n\n") if part.strip()]


def _connection():
    if psycopg is None:
        pytest.skip("psycopg is not installed")
    return psycopg.connect(
        os.getenv(
            "DATABASE_URL",
            "postgresql://workspace:workspace_dev_password@127.0.0.1:5433/workspace_ai_agent",
        )
    )


def _cleanup(connection):
    with connection.cursor() as cursor:
        cursor.execute(
            "DELETE FROM knowledge_document_version_sources WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute(
            "DELETE FROM knowledge_chunks WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute(
            "DELETE FROM knowledge_document_versions WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute(
            "DELETE FROM knowledge_sources WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute(
            "DELETE FROM knowledge_documents WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute(
            "DELETE FROM role_permissions WHERE role_id = %s",
            [ROLE_ID],
        )
        cursor.execute(
            "DELETE FROM user_roles WHERE user_id = %s",
            [USER_ID],
        )
        cursor.execute(
            "DELETE FROM organization_members WHERE organization_id = %s",
            [ORG_ID],
        )
        cursor.execute("DELETE FROM users WHERE id = %s", [USER_ID])
        cursor.execute("DELETE FROM roles WHERE id = %s", [ROLE_ID])
        cursor.execute("DELETE FROM organizations WHERE id = %s", [ORG_ID])
    connection.commit()


@pytest.mark.skipif(
    os.getenv("RUN_KNOWLEDGE_FULL_E2E") != "1",
    reason="set RUN_KNOWLEDGE_FULL_E2E=1",
)
def test_full_knowledge_e2e():
    connection = _connection()
    try:
        _cleanup(connection)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id FROM permissions
                WHERE resource = 'knowledge' AND action = 'read'
                """
            )
            permission = cursor.fetchone()
            if permission is None:
                pytest.fail(
                    "knowledge.read permission is missing; apply migration 052 before Full Knowledge E2E"
                )

            cursor.execute(
                """
                INSERT INTO organizations (id, name, organization_type, status)
                VALUES (%s, 'Knowledge Runtime E2E', 'workspace', 'active')
                """,
                [ORG_ID],
            )
            cursor.execute(
                """
                INSERT INTO users (id, name, email, status)
                VALUES (%s, 'Knowledge E2E User', 'knowledge-e2e@local.dev', 'active')
                """,
                [USER_ID],
            )
            cursor.execute(
                """
                INSERT INTO organization_members (organization_id, user_id, member_role, status)
                VALUES (%s, %s, 'member', 'active')
                """,
                [ORG_ID, USER_ID],
            )
            cursor.execute(
                """
                INSERT INTO roles (id, name, description)
                VALUES (%s, %s, 'Temporary role for Knowledge full E2E')
                """,
                [ROLE_ID, ROLE_NAME],
            )
            cursor.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                [USER_ID, ROLE_ID],
            )
            cursor.execute(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                [ROLE_ID, permission[0]],
            )
        connection.commit()

        content = (
            "Workspace Knowledge E2E stores canonical documents in PostgreSQL.\n\n"
            "Qdrant is the derived vector index, Ollama creates embeddings, "
            "and BGE reranks authorized candidates."
        )
        item = KnowledgeSourceItem(
            organization_id=ORG_ID,
            user_account_id=None,
            provider="runtime_e2e",
            resource_type="document",
            external_id="knowledge-e2e-001",
            content=content,
            source_checksum=hashlib.sha256(content.encode()).hexdigest(),
            title="Knowledge Runtime E2E",
            mime_type="text/plain",
            source_revision="1",
        )

        ollama = OllamaEmbeddingProvider(
            os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text-v2-moe"),
        )
        qdrant = QdrantVectorIndex(
            os.getenv("QDRANT_URL", "http://127.0.0.1:6333"),
            os.getenv("QDRANT_COLLECTION", "knowledge_v1"),
        )
        repository = PostgresKnowledgeRepository(connection)

        ingestion = KnowledgeIngestionService(
            repository=repository,
            authorization=AllowIngestion(),
            chunker=SimpleChunker(),
            embedding=ollama,
            vector_index=qdrant,
        )
        ingested = ingestion.ingest(item)

        assert ingested.status == "COMPLETED"
        assert ingested.source_id
        assert ingested.document_version_id
        assert ingested.chunk_count == 2

        semantic = KnowledgeRetrievalService(ollama, qdrant)
        reranked = RerankedKnowledgeRetrievalService(
            semantic,
            BGEReranker(
                model_name=os.getenv(
                    "BGE_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"
                )
            ),
        )
        authorization = PostgresKnowledgeAuthorizationRepository(connection)
        authorized = AuthorizedKnowledgeRetrievalService(reranked, authorization)

        assert authorization.authorize_query(
            user_id=USER_ID,
            organization_id=ORG_ID,
        )

        results = authorized.retrieve(
            "Where are canonical documents and embeddings stored?",
            user_id=USER_ID,
            organization_id=ORG_ID,
            candidate_limit=4,
            limit=2,
        )

        assert results
        assert any("PostgreSQL" in result.content for result in results)
        assert all(result.provider == "runtime_e2e" for result in results)
        assert all(result.external_id == "knowledge-e2e-001" for result in results)
        assert all(result.document_version_id == ingested.document_version_id for result in results)

        vietnamese_results = authorized.retrieve(
            "Dữ liệu tài liệu chuẩn và embedding được lưu ở đâu?",
            user_id=USER_ID,
            organization_id=ORG_ID,
            candidate_limit=4,
            limit=2,
        )

        assert vietnamese_results
        assert any("PostgreSQL" in result.content for result in vietnamese_results)
        assert all(result.provider == "runtime_e2e" for result in vietnamese_results)
        assert all(result.external_id == "knowledge-e2e-001" for result in vietnamese_results)
        assert all(
            result.document_version_id == ingested.document_version_id
            for result in vietnamese_results
        )

        assert not authorization.authorize_query(
            user_id=USER_ID,
            organization_id="9b2e6b6a-4d8a-4b72-8c1e-9d8e5b8a7199",
        )
    finally:
        _cleanup(connection)
        connection.close()
