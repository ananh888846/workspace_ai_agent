
"""
Created/Updated: 2026-09-24 20:32 GMT+7
Main Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.
"""

from dataclasses import dataclass

from app.application.knowledge.ports import (
    AuthorizationPort,
    ChunkerPort,
    EmbeddingPort,
    KnowledgeRepository,
    VectorIndexPort,
)
from app.domain.knowledge.source import KnowledgeSourceItem


@dataclass(frozen=True)
class IngestionResult:
    status: str
    source_id: str | None = None
    document_version_id: str | None = None
    chunk_count: int = 0


class KnowledgeIngestionService:
    """Coordinates ingestion; provider APIs stay outside this use-case."""

    def __init__(
        self,
        repository: KnowledgeRepository,
        authorization: AuthorizationPort,
        chunker: ChunkerPort,
        embedding: EmbeddingPort,
        vector_index: VectorIndexPort,
    ) -> None:
        self.repository = repository
        self.authorization = authorization
        self.chunker = chunker
        self.embedding = embedding
        self.vector_index = vector_index

    def ingest(self, item: KnowledgeSourceItem) -> IngestionResult:
        allowed = self.authorization.authorize_ingestion(
            organization_id=item.organization_id,
            user_account_id=item.user_account_id,
            provider=item.provider,
            resource_type=item.resource_type,
            external_id=item.external_id,
        )
        if not allowed:
            return IngestionResult(status="SKIPPED_UNAUTHORIZED")

        source = self.repository.create_source(item)

        if item.deleted:
            version_ids = self.repository.retire_source(source.id)
            for version_id in version_ids:
                self.vector_index.delete_document_version(version_id)
            return IngestionResult(status="DELETED", source_id=source.id)

        current_checksum = self.repository.current_checksum(source.id)
        chunks = self.chunker.chunk(item.content)

        if current_checksum == item.source_checksum:
            version_id = self.repository.current_version_id(source.id)
            if version_id is None:
                raise RuntimeError("knowledge_current_version_missing")

            if self.vector_index.is_indexed(version_id, len(chunks)):
                self.repository.mark_unchanged(source.id)
                return IngestionResult(
                    status="SKIPPED_UNCHANGED",
                    source_id=source.id,
                    document_version_id=version_id,
                    chunk_count=len(chunks),
                )

            # The canonical version exists, but its derived vector index is
            # incomplete or stale. Re-persist chunks and rebuild the same
            # deterministic Qdrant point IDs instead of creating a duplicate
            # PostgreSQL version.
            self.repository.create_chunks(
                version_id,
                item.organization_id,
                chunks,
            )
            if item.assets:
                self.repository.create_assets(
                    version_id,
                    item.organization_id,
                    item.assets,
                )
            vectors = self.embedding.embed(chunks)
            self.vector_index.upsert(
                chunks,
                vectors,
                version_id,
                item.organization_id,
            )
            self.vector_index.reconcile(
                version_id,
                list(range(len(chunks))),
            )
            return IngestionResult(
                status="REPAIRED_INDEX",
                source_id=source.id,
                document_version_id=version_id,
                chunk_count=len(chunks),
            )

        version = self.repository.create_document_version(source.id, item)
        self.repository.create_chunks(
            version.id,
            item.organization_id,
            chunks,
        )
        if item.assets:
            self.repository.create_assets(
                version.id,
                item.organization_id,
                item.assets,
            )
        vectors = self.embedding.embed(chunks)
        self.vector_index.upsert(chunks, vectors, version.id, item.organization_id)
        self.vector_index.reconcile(version.id, list(range(len(chunks))))

        previous_versions = self.repository.retire_previous_versions(
            source.id,
            version.id,
        )
        for previous_version_id in previous_versions:
            self.vector_index.delete_document_version(previous_version_id)

        return IngestionResult(
            status="COMPLETED",
            source_id=source.id,
            document_version_id=version.id,
            chunk_count=len(chunks),
        )
