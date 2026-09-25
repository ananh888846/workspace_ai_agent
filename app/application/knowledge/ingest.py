"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Coordinates authorized Knowledge ingestion from source item through chunks, embeddings, and vector indexing.\n"""\n\n"""\nCreated/Updated: 2026-09-24 20:32 GMT+7\nMain Function: Knowledge subsystem implementation or verification code for the Workspace AI Agent.\n"""\n\nfrom dataclasses import dataclass

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

        source = self.repository.find_source(item)
        if source is None:
            source = self.repository.create_source(item)

        current_checksum = self.repository.current_checksum(source.id)
        if current_checksum == item.source_checksum:
            self.repository.mark_unchanged(source.id)
            return IngestionResult(status="SKIPPED_UNCHANGED", source_id=source.id)

        version = self.repository.create_document_version(source.id, item)
        chunks = self.chunker.chunk(item.content)
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
        self.vector_index.reconcile(version.id)

        return IngestionResult(
            status="COMPLETED",
            source_id=source.id,
            document_version_id=version.id,
            chunk_count=len(chunks),
        )
